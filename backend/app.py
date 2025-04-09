import os

from dotenv import load_dotenv
from flask import Flask
from flask import render_template

from backend.admin import init_admin
from backend.config_dev import DevConfig
from backend.config_prod import ProdConfig
from backend.models import Car, Category
from backend.models import db

load_dotenv()  # Загружает переменные из .env

app = Flask(__name__)

Config = DevConfig if os.environ.get('FLASK_ENV') != 'production' else ProdConfig
app.config.from_object(Config)

# Инициализация расширений
db.init_app(app)

# Инициализация админки
init_admin(app)


@app.route('/')
def home():
    cars = Car.query.all()  # Или Car.query.limit(10).all() для ограничения количества
    categories = Category.query.all()  # Загружаем все категории для отображения в меню/фильтре
    return render_template('index.html', cars=cars, categories=categories)


@app.route('/car/<int:car_id>')
def car_details(car_id):
    car = Car.query.get_or_404(car_id)
    return render_template('car_details.html', car=car)


@app.route('/catalog')
def catalog():
    cars = Car.query.all()
    return render_template('catalog.html', cars=cars)


if __name__ == '__main__':
    with app.app_context():

        # Instance папка
        instance_path = os.path.join(app.instance_path)
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)

    app.run(debug=True)
