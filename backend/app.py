import os

from dotenv import load_dotenv
from flask import Blueprint
from flask import Flask
from flask import render_template, redirect, url_for, flash, request
from flask_login import LoginManager
from flask_login import login_user, logout_user, login_required
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired
from sqlalchemy.orm import joinedload

from backend.admin import init_admin
from backend.config_dev import DevConfig
from backend.config_prod import ProdConfig
from backend.models import Car, Category, Brand, Country, CarType
from backend.models import User
from backend.models import db

# .env
load_dotenv()

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
init_admin(app)

# Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'admin_login'
login_manager.init_app(app)


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


api = Blueprint('api', __name__)


@app.route('/api/import_car', methods=['POST'])
def import_car():
    from utils.telegram_import import import_car as handler
    return handler(request)


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
