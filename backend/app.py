from flask import Flask, render_template
from models import db, Car, Category
from admin import init_admin
import os

app = Flask(__name__)

# Конфигурация БД
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'cars.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Отключаем устаревшее поведение
app.config['SECRET_KEY'] = 'my-secret-key-test1'  # Замените на настоящий секретный ключ

# Инициализация расширений
db.init_app(app)

# Инициализация админки
init_admin(app)

@app.route('/')
def home():
    cars = Car.query.all()  # Или Car.query.limit(10).all() для ограничения количества
    categories = Category.query.all()  # Или Car.query.limit(10).all() для ограничения количества
    return render_template('index.html', cars=cars, categories=categories)

if __name__ == '__main__':
    with app.app_context():
        # Создаем папку instance если ее нет
        if not os.path.exists(os.path.join(basedir, 'instance')):
            os.makedirs(os.path.join(basedir, 'instance'))

        # Создаем таблицы (только для разработки!)
        # В продакшене используйте миграции Alembic
        db.create_all()

    app.run(debug=True)