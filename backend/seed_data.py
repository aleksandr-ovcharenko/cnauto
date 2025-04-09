from backend.models import db, Brand, CarType
from datetime import datetime
from backend.app import app



with app.app_context():
    brands = [
        {"name": "BYD", "slug": "byd", "logo": "byd.png"},
        {"name": "Chery", "slug": "chery", "logo": "chery.png"},
        {"name": "Geely", "slug": "geely", "logo": "geely.png"},
        {"name": "BMW", "slug": "bmw", "logo": "bmw.png"},
        {"name": "Volkswagen", "slug": "vw", "logo": "vw.png"},
        {"name": "Toyota", "slug": "toyota", "logo": "toyota.png"},
    ]

    types = [
        {"name": "Электро", "slug": "electric", "icon": "electric.png"},
        {"name": "Гибрид", "slug": "hybrid", "icon": "hybrid.png"},
        {"name": "Бензин", "slug": "petrol", "icon": "petrol.png"},
        {"name": "Дизель", "slug": "diesel", "icon": "diesel.png"},
    ]

    for b in brands:
        if not Brand.query.filter_by(slug=b["slug"]).first():
            db.session.add(Brand(**b, created_at=datetime.utcnow()))

    for t in types:
        if not CarType.query.filter_by(slug=t["slug"]).first():
            db.session.add(CarType(**t, created_at=datetime.utcnow()))

    db.session.commit()
    print("✅ Бренды и типы авто добавлены")
