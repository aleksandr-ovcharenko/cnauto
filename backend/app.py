import logging
import os

import requests
from dotenv import load_dotenv
from flask import Blueprint
from flask import Flask
from flask import Response
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager
from flask_login import login_user, logout_user, login_required
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from sqlalchemy.orm import joinedload
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired

# Use relative imports instead of backend.* package imports
from admin import init_admin
from app_decorators import admin_required
from config_dev import DevConfig
from config_prod import ProdConfig
from events import setup_deletion_events
from models import Car, Category, Brand, Country, CarType, User, db, ImageTask
from utils.file_logger import setup_file_logger
from utils.image_queue import start_image_processor
from utils.log_viewer import get_log_files, get_log_content
from utils.telegram_import import import_car as import_car_handler

# .env
load_dotenv()

# Import and set up file logging
log_file_path = setup_file_logger()

# Get the root logger
logger = logging.getLogger()

# Flask app
app = Flask(__name__)
env = os.getenv("FLASK_ENV", "development")
if env == "production":
    app.config.from_object(ProdConfig)
    logger.info("✅ ProdConfig loaded")
else:
    app.config.from_object(DevConfig)
    logger.info("✅ DevConfig loaded")

logger.info(f"📦 DB URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")


# Add a Flask handler to log all requests - with reduced verbosity
@app.before_request
def log_request_info():
    # Only log the request path and method, not the headers or body to avoid sensitive data
    logger = logging.getLogger('flask.request')
    logger.info(f"Request: {request.method} {request.path}")


# Add a handler to log all responses - with reduced verbosity
@app.after_request
def log_response_info(response):
    logger = logging.getLogger('flask.response')
    logger.info(f"Response: {response.status}")
    return response


# Init extensions
db.init_app(app)
app.config['MIGRATIONS_DIR'] = os.path.join(os.path.dirname(__file__), '../migrations')
migrate = Migrate(app, db)
admin_app = init_admin(app)

# Set up Cloudinary deletion event listeners
with app.app_context():
    setup_deletion_events()

    # Start the image processor worker for handling AI image generation
    image_processor_thread = start_image_processor(app)
    logger.info("✅ Image processor started for asynchronous AI image generation")

# Add a verification point to ensure logs are being captured
log_capture_test_interval = 60  # seconds


# Use Flask 2.0+ compatible approach for first request handling
def start_periodic_logging():
    """Start a background thread to periodically log verification messages"""
    import time
    import threading

    logger = logging.getLogger("runtime_verif")
    logger.info("🔄 Application started - verifying logging is working")

    def log_check_thread():
        count = 0
        while True:
            try:
                logger.info(f"⏱️ Periodic log check #{count} - logging is still active")
                count += 1
                # Sleep in smaller increments to be more responsive to shutdown
                for _ in range(log_capture_test_interval):
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Error in log check thread: {str(e)}")
                # Continue the loop even if there's an error
                time.sleep(5)

    # Create and start the thread
    t = threading.Thread(target=log_check_thread, daemon=True)
    t.name = "LogVerificationThread"  # Name the thread for easier debugging
    t.start()

    # Keep a reference to the thread to prevent garbage collection
    global log_verification_thread
    log_verification_thread = t

    logger.info(f"🧵 Started log verification thread: {t.name} (id: {t.ident})")


# Store a reference to the thread
log_verification_thread = None

# Start the periodic logging immediately
start_periodic_logging()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)  # Вернёт 404 если пользователя нет


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[InputRequired()])
    password = PasswordField('Пароль', validators=[InputRequired()])
    remember = BooleanField('Запомнить меня')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.has_role('admin'):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('admin_dashboard_main'))
        flash('Неверные данные для входа или недостаточно прав', 'error')
        logging.getLogger(__name__).warning('Неверные данные для входа или недостаточно прав')
    return render_template('admin/login.html', form=form)


@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    logging.getLogger(__name__).info('Вы вышли из системы')
    return redirect(url_for('admin_login'))


@app.route('/')
def home():
    cars = Car.query.all()  # Или Car.query.limit(10).all() для ограничения количества
    categories = Category.query.all()  # Загружаем все категории для отображения в меню/фильтре
    return render_template('index.html', cars=cars, categories=categories)


@app.route('/car/<int:car_id>', endpoint="car_page")
def car_details(car_id):
    car = Car.query.get_or_404(car_id)
    return render_template('car_details.html', car=car)


@app.template_filter('thumb_url')
def thumb_url_filter(url, width=400):
    """
    Convert a Cloudinary URL to a thumbnail URL with specified width
    Handles None values and invalid URLs gracefully
    """
    try:
        # Safely handle None values
        if url is None:
            logger.warning("⚠️ thumb_url_filter received None instead of a URL")
            return ""

        parts = url.split('/upload/')
        if len(parts) != 2:
            # Not a standard Cloudinary URL or already transformed
            return url
        return f"{parts[0]}/upload/w_{width},c_limit/{parts[1]}"
    except Exception as e:
        logger.error(f"⚠️ Ошибка в thumb_url_filter: {e}", exc_info=True)
        return url or ""


@app.template_filter('format_currency')
def format_currency_filter(price, currency_obj=None):
    """Format a price based on currency object or with defaults"""
    if not price:
        return "-"

    # Currency-specific locale mapping
    currency_locale_map = {
        'RUB': 'ru-RU',
        'USD': 'en-US',
        'EUR': 'de-DE',
        'GBP': 'en-GB',
        'CNY': 'zh-CN',
        'JPY': 'ja-JP'
    }

    if currency_obj:
        currency = currency_obj.code if currency_obj and currency_obj.code else 'RUB'
        # Use currency-specific locale if no explicit locale is set
        if currency_obj and currency_obj.locale:
            locale = currency_obj.locale.replace('_', '-')
        else:
            # Try to get locale from the currency code
            locale = currency_locale_map.get(currency, 'ru-RU')
        symbol = currency_obj.symbol if currency_obj and currency_obj.symbol else '₽'
    else:
        # Default to Russian locale and currency
        locale = 'ru-RU'
        currency = 'RUB'
        symbol = '₽'

    # Special case for Russian Rubles
    if currency == 'RUB':
        # Format with space as thousands separator and no decimal places
        try:
            # Try to convert to integer first to remove decimal part for whole numbers
            clean_price = float(price)
            formatted_price = f"{int(clean_price):,}".replace(',', ' ')
            return f"{formatted_price} {symbol}"
        except Exception as e:
            logger.error(f"Error formatting RUB price: {e}")
            # Fallback if any error occurs
            return f"{price} {symbol}"

    # Format with Babel for other currencies
    try:
        from babel.numbers import format_currency
        return format_currency(price, currency, locale=locale)
    except Exception as e:
        # Fallback to simpler formatting
        try:
            import locale as loc
            loc.setlocale(loc.LC_ALL, locale.replace('-', '_'))
            return loc.currency(price, symbol=symbol, grouping=True)
        except:
            # Last resort
            return f"{price:,.2f} {symbol}"


@app.route("/catalog")
def catalog():
    brand = request.args.get("brand")
    country_name = request.args.get("country")
    type_slugs = request.args.getlist('type')

    query = Car.query.options(joinedload(Car.currency))

    if brand:
        query = query.join(Car.brand).filter(Brand.slug == brand)
    if country_name:
        query = query.join(Car.brand).join(Brand.country).filter(Country.name == country_name)
    if type_slugs:
        query = query.join(Car.car_type).filter(CarType.slug.in_(type_slugs))

    cars = query.all()
    brands = Brand.query.order_by(Brand.name).all()
    countries = Country.query.order_by(Country.name).all()
    car_types = CarType.query.order_by(CarType.name).all()

    query_args = request.args.to_dict(flat=False)
    reset_type_args = query_args.copy()
    reset_type_args.pop('type', None)
    reset_type_url = url_for('catalog', **reset_type_args)

    return render_template("catalog.html", cars=cars, brands=brands, countries=countries, car_types=car_types,
                           reset_type_url=reset_type_url)


@app.route('/admin/logs')
@login_required
def view_logs():
    """
    Render the log viewer interface
    """
    log_files = get_log_files()
    selected_file = request.args.get('file')

    # If no file specified or file doesn't exist, use the most recent
    if not selected_file or selected_file not in log_files:
        selected_file = log_files[0] if log_files else None

    log_lines = []
    if selected_file:
        log_lines = get_log_content(selected_file)

    return render_template(
        'log_viewer.html',
        log_files=log_files,
        current_log=selected_file,
        log_lines=log_lines
    )


@app.route('/admin/logs/data')
@login_required
def get_logs_data():
    """
    API endpoint to get log data for auto-refresh
    """
    log_files = get_log_files()
    selected_file = request.args.get('file')

    # If no file specified or file doesn't exist, use the most recent
    if not selected_file or selected_file not in log_files:
        selected_file = log_files[0] if log_files else None

    log_lines = []
    if selected_file:
        log_lines = get_log_content(selected_file)

    return {
        'log_files': log_files,
        'current_log': selected_file,
        'log_lines': log_lines
    }


@app.route('/admin/logs/raw')
@login_required
def view_raw_log():
    """
    View raw log file content
    """
    log_files = get_log_files()
    selected_file = request.args.get('file')

    # If no file specified or file doesn't exist, use the most recent
    if not selected_file or selected_file not in log_files:
        selected_file = log_files[0] if log_files else None

    if not selected_file:
        return "No log files found", 404

    log_path = os.path.join(app.config['LOG_FOLDER'], selected_file)

    with open(log_path, 'r') as f:
        content = f.read()

    return Response(content, mimetype='text/plain')


@app.route('/admin/logs/files')
@login_required
def get_log_files_api():
    """
    API endpoint to get available log files
    """
    log_files = get_log_files()
    return jsonify(log_files)


@app.route('/admin/logs/content')
@login_required
def get_log_content_api():
    """
    API endpoint to get log content with filtering
    """
    log_files = get_log_files()
    selected_file = request.args.get('file')
    level_filter = request.args.get('level', 'all').lower()
    search_term = request.args.get('search', '')

    # If no file specified or file doesn't exist, use the most recent
    if not selected_file or selected_file not in log_files:
        selected_file = log_files[0] if log_files else None

    if not selected_file:
        return jsonify({"lines": []})

    log_lines = get_log_content(selected_file)

    # Apply level filter if not 'all'
    if level_filter != 'all':
        log_lines = [line for line in log_lines if line['level'].lower() == level_filter]

    # Apply search filter if provided
    if search_term:
        log_lines = [line for line in log_lines if search_term.lower() in line['message'].lower()]

    return jsonify({"lines": log_lines})


@app.route('/admin/api-docs')
@login_required
def api_docs():
    """Render the API documentation page"""
    return render_template('api_docs.html')


api = Blueprint('api', __name__)


@api.route('/import_car', methods=['POST'])
def import_car():
    return import_car_handler()


# Diagnostic route to help troubleshoot Telegram token issues
@api.route('/diagnose-telegram', methods=['GET'])
def diagnose_telegram():
    import json

    logger = logging.getLogger(__name__)

    # Check environment variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    token_status = "✅ Present" if bot_token else "❌ Missing"

    # Log to the file
    logger.info(f"TELEGRAM_BOT_TOKEN status: {token_status}")

    # Check other env vars
    env_vars = {key: "✅ Set" if os.getenv(key) else "❌ Missing"
                for key in ["FLASK_ENV", "IMPORT_API_TOKEN", "CLOUDINARY_URL"]}

    logger.info(f"Environment variables: {json.dumps(env_vars, indent=2)}")

    # Test token with a dummy request if available
    test_result = None
    if bot_token:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            logger.info(f"Testing Telegram API with URL: {url}")
            response = requests.get(url)
            response.raise_for_status()
            test_result = response.json()
            logger.info(f"Telegram API test successful: {json.dumps(test_result, indent=2)}")
        except Exception as e:
            test_result = {"error": str(e)}
            logger.error(f"Telegram API test failed: {str(e)}")

    # Return diagnostic info
    diagnostic_info = {
        "telegram_token_status": token_status,
        "env_vars": env_vars,
        "telegram_api_test": test_result,
        "log_file_path": log_file_path
    }

    # Also return info as plain text for easy viewing
    info_text = "\n".join([
        "===== TELEGRAM IMPORT DIAGNOSTIC =====",
        f"Telegram Token: {token_status}",
        f"Environment Variables: {json.dumps(env_vars, indent=2)}",
        f"Log File Path: {log_file_path}",
        "=====================================",
    ])

    logger.info(info_text)

    return f"<pre>{info_text}</pre>"


@api.route('/diagnose-replicate', methods=['GET'])
def diagnose_replicate():
    import json
    from utils.generator_photon import check_replicate_api_token

    logger = logging.getLogger(__name__)

    # Check environment variables
    api_token = os.getenv("REPLICATE_API_TOKEN")
    token_status = "✅ Present" if api_token else "❌ Missing"

    # Test token validity
    token_valid = "Unknown"
    if api_token:
        token_valid = "✅ Valid" if check_replicate_api_token() else "❌ Invalid"

    # Log to the file
    logger.info(f"REPLICATE_API_TOKEN status: {token_status}, validity: {token_valid}")

    # Check other env vars
    env_vars = {
        "REPLICATE_API_TOKEN": token_status,
        "REPLICATE_PHOTON_MODEL": os.getenv("REPLICATE_PHOTON_MODEL", "luma/photon"),
        "REPLICATE_MODE": os.getenv("REPLICATE_MODE", "photon"),
        "CLOUDINARY_URL": "✅ Set" if os.getenv("CLOUDINARY_URL") else "❌ Missing"
    }

    logger.info(f"Environment variables: {json.dumps(env_vars, indent=2)}")

    # Return diagnostic info
    diagnostic_info = {
        "replicate_token_status": token_status,
        "replicate_token_valid": token_valid,
        "env_vars": env_vars,
        "log_file_path": log_file_path
    }

    # Also return info as plain text for easy viewing
    info_text = "\n".join([
        "===== REPLICATE API DIAGNOSTIC =====",
        f"Replicate API Token: {token_status}",
        f"Token Validity: {token_valid}",
        f"Environment Variables: {json.dumps(env_vars, indent=2)}",
        f"Log File Path: {log_file_path}",
        "====================================="
    ])

    logger.info(info_text)

    return f"<pre>{info_text}</pre>"


@api.route('/image-tasks', methods=['GET'])
@login_required
def list_image_tasks():
    """
    Get a list of all image generation tasks or filter by car ID
    """
    from utils.image_queue import get_car_tasks, task_status

    car_id = request.args.get('car_id')

    if car_id:
        try:
            car_id = int(car_id)
            tasks = get_car_tasks(car_id)
            return jsonify({
                'car_id': car_id,
                'tasks': tasks
            })
        except ValueError:
            return jsonify({'error': 'Invalid car_id parameter'}), 400
    else:
        # Return all tasks (limited to most recent 50)
        all_tasks = list(task_status.values())
        all_tasks.sort(key=lambda x: x.get('last_update', ''), reverse=True)
        return jsonify({
            'tasks': all_tasks[:50],
            'total_count': len(all_tasks)
        })


@api.route('/image-tasks/<task_id>', methods=['GET'])
@login_required
def get_image_task(task_id):
    """
    Get details for a specific image generation task
    """
    from utils.image_queue import get_task_status

    task = get_task_status(task_id)

    if task['status'] == 'unknown':
        return jsonify({'error': 'Task not found'}), 404

    return jsonify(task)


@api.route('/image-tasks', methods=['GET'])
@login_required
@admin_required
def image_tasks_api():
    """
    API endpoint to get image task history
    
    Query parameters:
    - status: Filter by status (pending, processing, completed, failed)
    - source: Filter by source (gallery_ai, upload, telegram)
    - car_id: Filter by car ID
    - limit: Limit number of results (default 50)
    - offset: Offset for pagination
    """
    try:
        # Get query parameters
        status = request.args.get('status')
        source = request.args.get('source')
        car_id = request.args.get('car_id')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        # Build query
        query = ImageTask.query

        # Apply filters if provided
        if status:
            query = query.filter(ImageTask.status == status)
        if source:
            query = query.filter(ImageTask.source == source)
        if car_id:
            query = query.filter(ImageTask.car_id == car_id)

        # Order by newest first
        query = query.order_by(ImageTask.created_at.desc())

        # Apply pagination
        total = query.count()
        tasks = query.limit(limit).offset(offset).all()

        # Convert to dictionaries
        task_dicts = [task.to_dict() for task in tasks]

        # Return as JSON
        return jsonify({
            'total': total,
            'limit': limit,
            'offset': offset,
            'tasks': task_dicts
        })
    except Exception as e:
        logger.error(f"Error in image tasks API: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/admin/image-tasks', methods=['GET'])
@login_required
@admin_required
def image_tasks_view():
    """Web interface for viewing image task history"""
    return render_template('image_tasks.html')


@app.route('/admin/')
@admin_required
@login_required
def admin_dashboard_main():
    return render_template('admin/dashboard.html')


@app.route('/admin/dashboard')
@admin_required
@login_required
def admin_dashboard():
    return render_template('admin_dashboard.html')


import psutil
import platform
import datetime

# --- Admin Dashboard Stats Endpoints ---
@app.route('/admin/stats/server')
@admin_required
@login_required
def admin_stats_server():
    """Return server stats: CPU, memory, disk, uptime."""
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = (datetime.datetime.now() - boot_time).total_seconds()
    stats = {
        'cpu_percent': psutil.cpu_percent(interval=0.5),
        'memory': psutil.virtual_memory()._asdict(),
        'disk': psutil.disk_usage('/')._asdict(),
        'uptime_seconds': int(uptime),
        'platform': platform.platform(),
        'hostname': platform.node(),
        'boot_time': boot_time.isoformat(),
    }
    return jsonify(stats)

@app.route('/admin/stats/app')
@admin_required
@login_required
def admin_stats_app():
    """Return application stats stub."""
    # TODO: Replace with real queries
    stats = {
        'active_users': 0,  # Implement logic
        'visits_today': 0,  # Implement logic
        'recent_logins': [],
        'error_count_24h': 0,
        'queue_length': 0,
    }
    return jsonify(stats)

@app.route('/admin/stats/health')
@admin_required
@login_required
def admin_stats_health():
    """Return system health stub."""
    # TODO: Implement real checks
    stats = {
        'db_status': 'ok',
        'cache_status': 'ok',
        'worker_status': 'ok',
        'recent_deploy': None,
        'pending_updates': False,
    }
    return jsonify(stats)

@app.route('/admin/stats/visualizations')
@admin_required
@login_required
def admin_stats_visualizations():
    """Return data for dashboard visualizations."""
    # Example traffic data: hourly visits for the past 12 hours
    import datetime
    now = datetime.datetime.now()
    traffic = []
    for i in range(12):
        hour = (now - datetime.timedelta(hours=11-i)).strftime('%H:00')
        visits = 10 + (i * 7) % 23  # Dummy data, replace with real stats
        traffic.append({'hour': hour, 'visits': visits})
    stats = {
        'traffic': traffic,
        'cpu_history': [],
        'memory_history': [],
    }
    return jsonify(stats)

@app.route('/admin/stats/misc')
@admin_required
@login_required
def admin_stats_misc():
    """Return miscellaneous info."""
    stats = {
        'announcements': [],
        'version': os.getenv('APP_VERSION', 'dev'),
        'commit': os.getenv('GIT_COMMIT', ''),
    }
    return jsonify(stats)


app.register_blueprint(api, url_prefix='/api')

if __name__ == '__main__':
    with app.app_context():
        logger.info("🔗 login url: %s", url_for('admin_login'))

    with app.app_context():
        try:
            from alembic.config import Config
            from alembic import command
            from seeds.seed_brand_synonyms import seed_brand_synonyms

            # Путь к актуальному alembic.ini
            alembic_cfg = Config(os.path.join(os.path.dirname(__file__), '..', 'alembic.ini'))
            command.upgrade(alembic_cfg, 'head')
            logger.info("✅ Миграции применены")

        except Exception as e:
            logger.error("⚠️ Ошибка при миграции: %s", e)

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
