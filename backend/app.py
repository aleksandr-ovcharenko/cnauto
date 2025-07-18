import logging
import os

import requests
from dotenv import load_dotenv
from flask import Blueprint
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import logging
from logging.handlers import RotatingFileHandler
import time
from datetime import datetime, timedelta
import re
import json
import uuid
from dotenv import load_dotenv
import os
from flask_cors import CORS
from .admin import init_admin
from .app_decorators import admin_required
from .config_dev import DevConfig
from .config_prod import ProdConfig
from .db import db
from .events import setup_deletion_events
from .models import Car, Category, Brand, Country, CarType, User, ImageTask
from .utils.file_logger import setup_file_logger
from .utils.image_queue import start_image_processor
from .utils.log_viewer import get_log_files, get_log_content
from .utils.telegram_import import import_car as import_car_handler

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

# Add Python built-ins to Jinja environment
app.jinja_env.globals['min'] = min
app.jinja_env.globals['max'] = max

# Initialize database and migrations
db.init_app(app)
migrate = Migrate(app, db, directory=os.path.join(os.path.dirname(__file__), 'migrations'))

# Add CORS support
CORS(app)  # Allow cross-origin requests, can be configured further if needed


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


# Set migrations directory path correctly - works in both local and remote environments
migrations_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'migrations'))
app.config['ALEMBIC_MIGRATION_PATH'] = migrations_dir
app.config['FLASK_MIGRATE_MIGRATIONS_DIRECTORY'] = migrations_dir


# === AUTOMATIC MIGRATION CHECK & UPGRADE ===
def auto_migrate_and_seed(app, db, migrations_dir):
    import logging
    from alembic.migration import MigrationContext
    from alembic.script import ScriptDirectory
    from alembic.config import Config
    from alembic import command
    from sqlalchemy import inspect

    logger = logging.getLogger()
    with app.app_context():
        try:
            # Connect to DB and get current revision
            connection = db.engine.connect()
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()

            # Prepare Alembic config
            alembic_ini_path = os.path.join(os.path.dirname(migrations_dir), 'alembic.ini')
            alembic_cfg = Config(alembic_ini_path)
            script = ScriptDirectory.from_config(alembic_cfg)
            head_rev = script.get_heads()[0]

            if not current_rev:
                logger.warning("⚠️ Database may not be migrated. Running upgrade...")
                command.upgrade(alembic_cfg, 'head')
                logger.info("✅ Database migrated to latest revision.")
            elif current_rev != head_rev:
                logger.warning(f"⚠️ Database is at version {current_rev} but latest is {head_rev}. Running upgrade...")
                command.upgrade(alembic_cfg, 'head')
                logger.info("✅ Database migrated to latest revision.")
            else:
                logger.info("✅ Database schema is up to date, no migration needed.")
            
            # Additionally check for the image_tasks table specifically
            inspector = inspect(db.engine)
            if 'image_tasks' not in inspector.get_table_names():
                logger.warning("⚠️ image_tasks table not found in database, creating it...")
                try:
                    from backend.models import ImageTask
                    ImageTask.__table__.create(db.engine)
                    logger.info("✅ Successfully created image_tasks table")
                except Exception as e:
                    logger.error(f"❌ Error creating image_tasks table: {e}")
            
            connection.close()
        except Exception as e:
            logger.error(f"❌ Error checking/applying migrations: {e}")
            return

        # === RUN SEEDS ===
        try:
            logger.info("🌱 Starting database seed process...")
            from .seeds.seed_brands import seed_brands
            from .seeds.seed_brand_synonyms import seed_brand_synonyms
            from .seeds.brand_models import seed_brand_models
            from .seeds.brand_trims import seed_brand_trims
            from .seeds.brand_modifications import seed_brand_modifications
            from .seeds.seed_categories import seed_categories
            from .seeds.seed_countries import seed_countries
            from .seeds.seed_currencies import seed_currencies

            # Prepare a session for scripts that require it
            session_factory = sessionmaker(bind=db.engine)
            Session = scoped_session(session_factory)

            logger.info("🌱 Seeding countries...")
            seed_countries()
            logger.info("🌱 Seeding brands...")
            seed_brands()
            logger.info("🌱 Seeding brand synonyms...")
            seed_brand_synonyms()
            logger.info("🌱 Seeding brand models...")
            seed_brand_models()
            logger.info("🌱 Seeding brand trims...")
            seed_brand_trims(Session())
            logger.info("🌱 Seeding brand modifications...")
            seed_brand_modifications(Session())
            logger.info("🌱 Seeding categories...")
            seed_categories()
            logger.info("🌱 Seeding currencies...")
            seed_currencies()
            logger.info("✅ All database seeds completed successfully!")
        except Exception as e:
            logger.error(f"❌ Error during database seeding: {e}")


# Call this BEFORE app.run() or exposing the WSGI app
import os

# switching off migration process for now
# if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
#     auto_migrate_and_seed(app, db, migrations_dir)

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
def format_currency_filter_wrapper(price, currency_obj=None):
    """
    Wrapper for the format_currency_filter function imported from the backend package.
    This wrapper allows the function to be used as a template filter.
    """
    from backend import format_currency_filter
    return format_currency_filter(price, currency_obj)


@app.route("/catalog")
@app.route("/catalog/")
def catalog():
    brand = request.args.get("brand")
    country_name = request.args.get("country")
    type_slugs = request.args.getlist('type')
    
    # Get page number from query parameter, default to page 1
    try:
        page = int(request.args.get('page', 1))
        if page < 1:
            # If page is less than 1, redirect to page 1
            args = request.args.copy()
            args['page'] = 1
            return redirect(url_for('catalog', **args))
    except ValueError:
        # If page is not a valid integer, redirect to page 1
        args = request.args.copy()
        args['page'] = 1
        return redirect(url_for('catalog', **args))
        
    per_page = 10  # Number of cars per page
    
    query = Car.query.options(joinedload(Car.currency))

    if brand:
        query = query.join(Car.brand).filter(Brand.slug == brand)
    if country_name:
        query = query.join(Car.brand).join(Brand.country).filter(Country.name == country_name)
    if type_slugs:
        query = query.join(Car.car_type).filter(CarType.slug.in_(type_slugs))

    # Sort cars by ID in descending order (newest first)
    query = query.order_by(Car.id.desc())
    
    # Get total count before pagination for validation
    total_count = query.count()
    total_pages = (total_count + per_page - 1) // per_page  # Ceiling division
    
    # If requested page exceeds max pages, redirect to last page
    if page > total_pages > 0:
        args = request.args.copy()
        args['page'] = total_pages
        return redirect(url_for('catalog', **args))
    
    # Implement pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    cars = pagination.items
    
    brands = Brand.query.order_by(Brand.name).all()
    countries = Country.query.order_by(Country.name).all()
    car_types = CarType.query.order_by(CarType.name).all()

    query_args = request.args.to_dict(flat=False)
    # Remove page from args when building reset URL
    reset_type_args = query_args.copy()
    reset_type_args.pop('type', None)
    reset_type_url = url_for('catalog', **reset_type_args)
    
    # Create base URL for pagination (preserving all filters)
    pagination_args = query_args.copy()
    if 'page' in pagination_args:
        pagination_args.pop('page')
    
    return render_template("catalog.html", 
                           cars=cars, 
                           brands=brands, 
                           countries=countries, 
                           car_types=car_types,
                           pagination=pagination,
                           pagination_args=pagination_args,
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


def get_cars():
    cars = Car.query.all()
    return jsonify([{
        'id': car.id,
        'model': car.model,
        'brand': car.brand.name if car.brand else None,
        'price': car.price
    } for car in cars])  # Simple serialization; expand as needed


api.add_url_rule('/cars', 'get_cars', view_func=get_cars, methods=['GET'])


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
    from .utils.generator_photon import check_replicate_api_token

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
    Get a paginated list of image generation tasks with filtering options
    
    Query parameters:
    - car_id: Filter by car ID
    - status: Filter by status (pending, processing, completed, failed)
    - source: Filter by source (ai_generation, upload, telegram, etc.)
    - page: Page number for pagination (default: 1)
    - per_page: Number of items per page (default: 20, max: 100)
    """
    from .models import ImageTask, db
    from sqlalchemy import desc
    
    try:
        # Build query with filters
        query = ImageTask.query
        
        # Apply filters
        car_id = request.args.get('car_id')
        if car_id:
            query = query.filter_by(car_id=int(car_id))
            
        status = request.args.get('status')
        if status in ['pending', 'processing', 'completed', 'failed']:
            query = query.filter_by(status=status)
            
        source = request.args.get('source')
        if source:
            query = query.filter_by(source=source)
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Execute query with pagination
        pagination = query.order_by(desc(ImageTask.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Prepare response
        tasks = [task.to_dict() for task in pagination.items]
        
        return jsonify({
            'tasks': tasks,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching image tasks: {str(e)}")
        return jsonify({'error': 'Failed to fetch image tasks'}), 500


@api.route('/image-tasks/<task_id>', methods=['GET'])
@login_required
def get_image_task(task_id):
    """
    Get details for a specific image generation task
    
    Returns:
        200: Task details
        404: If task not found
    """
    from .models import ImageTask
    
    try:
        task = ImageTask.query.filter_by(task_id=task_id).first()
        if not task:
            # Check in-memory status as fallback
            from .utils.image_queue import get_task_status
            mem_task = get_task_status(task_id)
            if mem_task.get('status') == 'unknown':
                return jsonify({'error': 'Task not found'}), 404
            return jsonify(mem_task)
            
        return jsonify(task.to_dict())
        
    except Exception as e:
        current_app.logger.error(f"Error fetching task {task_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch task details'}), 500


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
    """
    Web interface for viewing image task history
    
    Query parameters:
    - status: Filter by status (pending, processing, completed, failed)
    - source: Filter by source
    - car_id: Filter by car ID
    """
    from .models import ImageTask, db
    from sqlalchemy import desc
    
    try:
        # Get filter parameters
        status = request.args.get('status')
        source = request.args.get('source')
        car_id = request.args.get('car_id')
        
        # Build query
        query = ImageTask.query
        
        if status in ['pending', 'processing', 'completed', 'failed']:
            query = query.filter_by(status=status)
        if source:
            query = query.filter_by(source=source)
        if car_id and car_id.isdigit():
            query = query.filter_by(car_id=int(car_id))
        
        # Get paginated results
        page = request.args.get('page', 1, type=int)
        per_page = 20  # Items per page
        
        tasks = query.order_by(desc(ImageTask.created_at))\
                    .paginate(page=page, per_page=per_page, error_out=False)
        
        # Get filter options for the UI
        statuses = db.session.query(
            ImageTask.status.distinct().label('status')
        ).all()
        
        sources = db.session.query(
            ImageTask.source.distinct().label('source')
        ).filter(ImageTask.source.isnot(None)).all()
        
        return render_template(
            'image_tasks.html',
            tasks=tasks,
            statuses=[s.status for s in statuses],
            sources=[s.source for s in sources],
            current_filters={
                'status': status,
                'source': source,
                'car_id': car_id
            }
        )
        
    except Exception as e:
        current_app.logger.error(f"Error in image_tasks_view: {str(e)}")
        return render_template('error.html', error="Failed to load image tasks"), 500


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
        hour = (now - datetime.timedelta(hours=11 - i)).strftime('%H:00')
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

# Register filters
app.jinja_env.filters['format_currency'] = format_currency_filter_wrapper
app.jinja_env.filters['thumb_url'] = thumb_url_filter

if __name__ == '__main__':
    with app.app_context():
        logger.info("🔗 login url: %s", url_for('admin_login'))

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
