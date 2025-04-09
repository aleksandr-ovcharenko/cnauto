from flask import Flask
from models import db
from admin import init_admin

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cars.db'
app.config['SECRET_KEY'] = 'your-secret-key'

# Сначала инициализируем db
db.init_app(app)

# Затем админку
init_admin(app)

@app.route('/')
def home():
    return "Главная страница"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)