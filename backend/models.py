from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

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
    form_columns = ['model', 'price', 'currency', 'image', 'brand_logo', 'description', 'in_stock', 'category', 'brand',
                    'car_type']
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

    modification = db.Column(db.String(100))
    trim = db.Column(db.String(100))

    def __str__(self):
        # Display as: Brand Model Modification Trim (Price ₽)
        brand = self.brand.name if self.brand else ''
        model = self.model or ''
        modification = self.modification or ''
        trim = self.trim or ''
        parts = [brand, model, modification, trim]
        name = ' '.join([p for p in parts if p]).strip()
        return f'{name} ({self.price} ₽)'

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
    trims = db.relationship('BrandTrim', backref='brand', lazy='dynamic')
    modifications = db.relationship('BrandModification', backref='brand', lazy='dynamic')
    models = db.relationship('BrandModel', backref='brand', lazy='dynamic')

    def __str__(self):
        return self.name


class BrandSynonym(db.Model):
    __tablename__ = 'brand_synonyms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)  # "бмв", "BMW", "bmw"
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)


class BrandTrim(db.Model):
    """Model to store brand-specific trim levels"""
    __tablename__ = 'brand_trims'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)  # "SE", "Sport", "FLAGSHIP", etc.
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    source = db.Column(db.String(50))  # "user", "api", "auto_detected", etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('name', 'brand_id', name='unique_trim_per_brand'),
    )
    
    def __str__(self):
        return f"{self.name}"


class BrandModification(db.Model):
    """Model to store brand-specific modification types"""
    __tablename__ = 'brand_modifications'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    description = db.Column(db.String(200))
    source = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint('name', 'brand_id', name='unique_modification_per_brand'),
    )

    def __str__(self):
        return f"{self.name}"


class BrandModel(db.Model):
    __tablename__ = 'brand_models'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    is_multi_word = db.Column(db.Boolean, default=False)
    source = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint('name', 'brand_id', name='unique_model_per_brand'),
    )


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
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    locale = db.Column(db.String(20), nullable=True)
    cars = db.relationship('Car', back_populates='currency')

    def __str__(self):
        return f"{self.code} - {self.name}"


class CarEngine(db.Model):
    """Model to store engine information for cars"""
    __tablename__ = 'car_engines'
    
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
    
    # Basic engine data
    displacement = db.Column(db.String(20), nullable=True)  # Объем двигателя или батареи (например, "1.6T" или "77.4 kWh")
    power_hp = db.Column(db.Integer, nullable=True)        # Мощность в лошадиных силах
    type = db.Column(db.String(20), nullable=True)         # Тип двигателя (gasoline, diesel, hybrid, electric)
    drive = db.Column(db.String(20), nullable=True)        # Тип привода (front_wheel_drive, rear_wheel_drive, all_wheel_drive, etc.)
    transmission = db.Column(db.String(20), nullable=True) # Коробка передач (manual, automatic, cvt, dsg, etc.)
    
    # Original text and description
    engine_text = db.Column(db.String(100), nullable=True)  # Original parsed text
    description = db.Column(db.String(255), nullable=True)  # Generated or imported description
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    car = db.relationship('Car', backref=db.backref('engine_details', uselist=False))
    
    def generate_description(self):
        """Generate a human-readable engine description"""
        parts = []
        if self.displacement:
            parts.append(str(self.displacement))
        if self.power_hp:
            parts.append(f"{self.power_hp} л.с.")
        if self.drive:
            # Map drive type to Russian text
            drive_map = {
                "front_wheel_drive": "передний привод", 
                "rear_wheel_drive": "задний привод",
                "all_wheel_drive": "полный привод",
                "quattro": "quattro",
                "xdrive": "xDrive",
                "e_four": "E-Four"
            }
            drive_text = drive_map.get(self.drive, self.drive)
            parts.append(drive_text)
        if self.transmission:
            parts.append(f"КПП: {self.transmission}")
        
        return ", ".join(parts) if parts else (self.description or "-")
    
    def __str__(self):
        return self.generate_description()


class ImageTask(db.Model):
    """Model to track history of image generation and upload tasks"""
    __tablename__ = 'image_tasks'

    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=True)
    car = db.relationship('Car', backref='image_tasks')

    # Source can be: 'gallery_ai', 'upload', 'telegram', etc.
    source = db.Column(db.String(50), nullable=False)

    # Status: 'pending', 'processing', 'completed', 'failed'
    status = db.Column(db.String(20), default='pending')

    # Original image if AI generation
    source_image_id = db.Column(db.Integer, db.ForeignKey('car_images.id'), nullable=True)
    source_image = db.relationship('CarImage', foreign_keys=[source_image_id])

    # Result image (if any)
    result_image_id = db.Column(db.Integer, db.ForeignKey('car_images.id'), nullable=True)
    result_image = db.relationship('CarImage', foreign_keys=[result_image_id])

    # Store any prompt used for generation
    prompt = db.Column(db.Text, nullable=True)

    # Error message if failed
    error = db.Column(db.Text, nullable=True)

    # URLs for source and result
    source_url = db.Column(db.String(512), nullable=True)
    result_url = db.Column(db.String(512), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __str__(self):
        return f"ImageTask #{self.id} ({self.source}) - {self.status}"

    def to_dict(self):
        """Convert task to dictionary for API responses"""
        return {
            'id': self.id,
            'car_id': self.car_id,
            'car_model': self.car.model if self.car else None,
            'source': self.source,
            'status': self.status,
            'source_image_id': self.source_image_id,
            'result_image_id': self.result_image_id,
            'prompt': self.prompt,
            'error': self.error,
            'source_url': self.source_url,
            'result_url': self.result_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
