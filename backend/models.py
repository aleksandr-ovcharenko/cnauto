from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Text

db = SQLAlchemy()

user_roles = db.Table(
    'user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'))
)


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True)
    password_hash = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)

    roles = db.relationship('Role', secondary=user_roles, backref='users', lazy='subquery')

    def get_roles_display(self):
        return ', '.join(role.name for role in self.roles)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # admin, staff, customer
    description = db.Column(db.String(255))


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    icon = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Category {self.name}>'

    def __str__(self):
        return f'{self.name}'


class CarImage(db.Model):
    __tablename__ = 'car_images'

    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)

    url = db.Column(db.String(512), nullable=False)
    title = db.Column(db.String(100), nullable=True)
    alt = db.Column(db.String(255), nullable=True)
    position = db.Column(db.Integer, default=0)

    car = db.relationship('Car', back_populates='gallery_images')


class Car(db.Model):
    __tablename__ = 'cars'
    form_columns = ['model', 'price', 'currency', 'image', 'brand_logo', 'description', 'in_stock', 'category', 'brand', 'car_type']
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey('currencies.id'), nullable=True)
    currency = db.relationship('Currency', back_populates='cars')
    image_url = db.Column(db.String(300), nullable=True)
    brand_logo = db.Column(db.String(200))
    images = db.Column(db.JSON)
    description = db.Column(db.Text)
    in_stock = db.Column(db.Boolean, default=False)
    year = db.Column(db.String(50))
    mileage = db.Column(db.String(50))
    engine = db.Column(db.String(100))
    extras = db.Column(db.Text)
    price_fob = db.Column(db.String(100))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    category = db.relationship('Category', backref='cars')
    gallery_images = db.relationship(
        'CarImage',
        back_populates='car',
        order_by=lambda: CarImage.position,
        cascade='all, delete-orphan'
    )
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'))
    brand = db.relationship('Brand', backref='cars')

    car_type_id = db.Column(db.Integer, db.ForeignKey('car_types.id'))
    car_type = db.relationship('CarType', backref='cars')
    car_type_slug = db.Column(db.String(50))

    def __str__(self):
        return f'{self.model} ({self.price} ₽)'

    @property
    def formatted_price(self):
        return f"{self.price:,.0f} ₽".replace(",", " ")


class Brand(db.Model):
    __tablename__ = 'brands'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    logo = db.Column(db.String(200))
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'))
    country = db.relationship('Country', backref='brands')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    synonyms = db.relationship('BrandSynonym', backref='brand', lazy='dynamic')  # используем backref только здесь

    def __str__(self):
        return self.name


class BrandSynonym(db.Model):
    __tablename__ = 'brand_synonyms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)  # "бмв", "BMW", "bmw"
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)


class CarType(db.Model):
    __tablename__ = 'car_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    icon = db.Column(db.String(200))  # путь к иконке
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __str__(self):
        return self.name


class Country(db.Model):
    __tablename__ = 'countries'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __str__(self):
        return self.name


class Currency(db.Model):
    __tablename__ = 'currencies'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)  # e.g. 'RUB', 'USD'
    name = db.Column(db.String(50), nullable=False)  # e.g. 'Russian Ruble'
    symbol = db.Column(db.String(10), nullable=False)  # e.g. '₽', '$'
    locale = db.Column(db.String(20), nullable=True)  # e.g. 'ru_RU', 'en_US'
    cars = db.relationship('Car', back_populates='currency')

    def __str__(self):
        return f"{self.code} ({self.symbol}, {self.locale})" if self.locale else f"{self.code} ({self.symbol})"
