import logging
import os

from dotenv import load_dotenv
from flask import Blueprint
from flask import Flask
from flask import render_template, redirect, url_for, flash, request
from flask_login import LoginManager
from flask_login import login_user, logout_user, login_required
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from sqlalchemy.orm import joinedload
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired

from backend.admin import init_admin
from backend.config_dev import DevConfig
from backend.config_prod import ProdConfig
from backend.models import Car, Category, Brand, Country, CarType
from backend.models import User
from backend.models import db
from backend.utils.file_logger import setup_file_logger
from backend.utils.log_viewer import get_log_files, get_log_content
from backend.utils.telegram_import import import_car as import_car_handler
from backend.events import setup_deletion_events

# .env
load_dotenv()

# Import and set up file logging
log_file_path = setup_file_logger()

# Get the root logger
logger = logging.getLogger()

# Force debug logger output on startup to verify logging works
logger.debug("🔍 DEBUG logging is enabled")
logger.info("ℹ️ INFO logging is enabled")
logger.warning("⚠️ WARNING logging is enabled")
logger.error("❌ ERROR logging is enabled - this is just a test")

# Flask app
app = Flask(__name__)
env = os.getenv("FLASK_ENV", "development")
if env == "production":
    app.config.from_object(ProdConfig)
    print("✅ ProdConfig загружен")
else:
    app.config.from_object(DevConfig)
    print("✅ DevConfig загружен")

print("📦 DB URI:", app.config.get("SQLALCHEMY_DATABASE_URI"))

# Init extensions
db.init_app(app)
app.config['MIGRATIONS_DIR'] = os.path.join(os.path.dirname(__file__), '../migrations')
migrate = Migrate(app, db)
admin_app = init_admin(app)

# Set up Cloudinary deletion event listeners
with app.app_context():
    setup_deletion_events()

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
            return redirect(url_for('admin.index'))
        flash('Неверные данные для входа или недостаточно прав', 'error')
    return render_template('admin/login.html', form=form)


@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
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
    try:
        parts = url.split('/upload/')
        if len(parts) != 2:
            return url
        return f"{parts[0]}/upload/w_{width},c_limit/{parts[1]}"
    except Exception as e:
        print(f"⚠️ Ошибка в thumb_url_filter: {e}")
        return url


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
            print(f"Error formatting RUB price: {e}")
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
    
    content = "No log file available"
    if selected_file:
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        log_path = os.path.join(log_dir, selected_file)
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            content = f"Error reading log file: {str(e)}"
    
    # Return as plain text with proper content type
    return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}


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
        import requests
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            response = requests.get(url, timeout=5)
            test_result = response.json()
            logger.info(f"Telegram API test: {json.dumps(test_result, indent=2)}")
        except Exception as e:
            test_result = {"error": str(e)}
            logger.error(f"Telegram API test failed: {str(e)}")

    # Return diagnostic info
    diagnostic_info = {
        "telegram_token_status": token_status,
        "environment_variables": env_vars,
        "telegram_api_test": test_result,
        "log_file_path": log_file_path
    }

    # Also return info as plain text for easy viewing
    info_text = "\n".join([
        "===== TELEGRAM IMPORT DIAGNOSTIC =====",
        f"TELEGRAM_BOT_TOKEN: {token_status}",
        f"Environment Variables: {json.dumps(env_vars, indent=2)}",
        f"Telegram API Test: {json.dumps(test_result, indent=2) if test_result else 'Not tested (no token)'}",
        f"Log File Path: {log_file_path}",
        "=====================================",
    ])

    logger.info(info_text)

    return f"<pre>{info_text}</pre>"


app.register_blueprint(api, url_prefix='/api')

if __name__ == '__main__':
    with app.app_context():
        print("🔗 login url:", url_for('admin_login'))

    with app.app_context():
        try:
            from alembic.config import Config
            from alembic import command
            from backend.seeds.seed_brand_synonyms import seed_brand_synonyms

            # Путь к актуальному alembic.ini
            alembic_cfg = Config(os.path.join(os.path.dirname(__file__), '..', 'alembic.ini'))
            command.upgrade(alembic_cfg, 'head')
            print("✅ Миграции применены")

        except Exception as e:
            print("⚠️ Ошибка при миграции:", e)

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
