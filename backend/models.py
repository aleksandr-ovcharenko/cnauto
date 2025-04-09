from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    icon = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Category {self.name}>'

    def __str__(self):
        return f'{self.name}'

class Car(db.Model):
    __tablename__ = 'cars'
    form_columns = ['model', 'price', 'image', 'brand_logo', 'description', 'in_stock', 'category']
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False, index=True)
    image = db.Column(db.String(200))
    brand_logo = db.Column(db.String(200))
    images = db.Column(db.JSON)  # Для хранения списка дополнительных изображений
    description = db.Column(db.Text)  # Подробное описание
    in_stock = db.Column(db.Boolean, default=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    category = db.relationship('Category', backref='cars')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Метод для отображения в админке
    def __str__(self):
        return f'{self.model} ({self.price} ₽)'

    @property
    def formatted_price(self):
        return f"{self.price:,.0f} ₽".replace(",", " ")