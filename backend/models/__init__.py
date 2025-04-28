from enum import Enum
from datetime import datetime

class EngineType(Enum):
    """Engine types"""
    GASOLINE = "gasoline"
    DIESEL = "diesel"
    HYBRID = "hybrid"
    PLUGIN_HYBRID = "plugin_hybrid"
    ELECTRIC = "electric"
    LPG = "lpg"
    CNG = "cng"
    HYDROGEN = "hydrogen"


class DriveType(Enum):
    """Drive types"""
    FWD = "front_wheel_drive"
    RWD = "rear_wheel_drive"
    AWD = "all_wheel_drive"
    QUATTRO = "quattro"
    XDRIVE = "xdrive"
    E_FOUR = "e_four"


class TransmissionType(Enum):
    """Transmission types"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    CVT = "cvt"
    DCT = "dct"
    DSG = "dsg"
    PDK = "pdk"
    AMT = "amt"


# Import existing models from the app directly for now
try:
    from app import db
    
    class Brand(db.Model):
        __tablename__ = 'brands'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), unique=True, nullable=False)
        country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=True)
        logo = db.Column(db.String(255), nullable=True)
        synonyms = db.Column(db.String(255), nullable=True)
    
    class Country(db.Model):
        __tablename__ = 'countries'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), unique=True, nullable=False)
    
    class BrandModel(db.Model):
        __tablename__ = 'brand_models'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
        is_multi_word = db.Column(db.Boolean, default=False)
        
        # Relationships
        brand = db.relationship('Brand', backref=db.backref('models', lazy=True))
        
        __table_args__ = (
            db.UniqueConstraint('name', 'brand_id', name='unique_model_per_brand'),
        )
    
    class BrandTrim(db.Model):
        __tablename__ = 'brand_trims'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
        source = db.Column(db.String(50))
        
        # Relationships
        brand = db.relationship('Brand', backref=db.backref('trims', lazy=True))
        
        __table_args__ = (
            db.UniqueConstraint('name', 'brand_id', name='unique_trim_per_brand'),
        )

    class BrandModification(db.Model):
        __tablename__ = 'brand_modifications'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
        source = db.Column(db.String(50))
        
        # Relationships
        brand = db.relationship('Brand', backref=db.backref('modifications', lazy=True))
        
        __table_args__ = (
            db.UniqueConstraint('name', 'brand_id', name='unique_modification_per_brand'),
        )
    
    class CarEngine(db.Model):
        """Engine information stored with a car"""
        __tablename__ = 'car_engines'
        
        id = db.Column(db.Integer, primary_key=True)
        car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
        
        # Basic engine data
        displacement = db.Column(db.String(20), nullable=True)  # Объем двигателя или батареи (например, "1.6T" или "77.4 kWh")
        power_hp = db.Column(db.Integer, nullable=True)        # Мощность в лошадиных силах
        type = db.Column(db.String(20), nullable=True)         # Тип двигателя (EngineType)
        drive = db.Column(db.String(20), nullable=True)        # Тип привода (DriveType)
        transmission = db.Column(db.String(20), nullable=True) # Коробка передач
        
        # Original text and description
        engine_text = db.Column(db.String(100), nullable=True)  # Original parsed text
        description = db.Column(db.String(255), nullable=True)  # Generated or imported description
        
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        # Relationship
        car = db.relationship('Car', backref=db.backref('engine', uselist=False))
        
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
        
        def __repr__(self):
            return self.generate_description()
            
except (ImportError, RuntimeError):
    # When running tests, we may not have the app context
    # Just define the enums for the tests to use
    print("Note: Using stub models for testing")
    
    class Brand:
        pass
        
    class Country:
        pass
        
    class BrandModel:
        pass
        
    class BrandTrim:
        pass
        
    class BrandModification:
        pass
        
    class CarEngine:
        pass
        
    class Car:
        pass
        
    class BrandSynonym:
        pass
