import os

from dotenv import load_dotenv
from flask import Flask
from flask import render_template, redirect, url_for, flash, request
from flask_login import LoginManager
from flask_login import login_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired

from backend.admin import init_admin
from config_dev import DevConfig
from config_prod import ProdConfig
from backend.models import Car, Category, Brand, Country, CarType
from backend.models import User
from backend.models import db

load_dotenv()  # Загружает переменные из .env

app = Flask(__name__)

Config = DevConfig if os.environ.get('FLASK_ENV') != 'production' else ProdConfig
app.config.from_object(Config)

print("📦 DATABASE_URL:", os.getenv('DATABASE_URL'))
print("📦 DB URI:", app.config['SQLALCHEMY_DATABASE_URI'])


# Инициализация расширений
db.init_app(app)

with app.app_context():
    db.create_all()

# Инициализация админки
init_admin(app)

login_manager = LoginManager()
login_manager.login_view = 'admin_login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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


@app.route('/car/<int:car_id>')
def car_details(car_id):
    car = Car.query.get_or_404(car_id)
    return render_template('car_details.html', car=car)


@app.route("/catalog")
def catalog():
    brand = request.args.get("brand")
    country_name = request.args.get("country")
    type_slugs = request.args.getlist('type')

    query = Car.query

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


if __name__ == '__main__':
    with app.app_context():

        # Instance папка
        instance_path = os.path.join(app.instance_path)
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)

        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

