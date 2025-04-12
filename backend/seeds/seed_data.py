from datetime import datetime

from backend.models import db, CarType


def seed_types():
    types = [
        {"name": "Электро", "slug": "electric", "icon": "electric.png"},
        {"name": "Гибрид", "slug": "hybrid", "icon": "hybrid.png"},
        {"name": "Бензин", "slug": "petrol", "icon": "petrol.png"},
        {"name": "Дизель", "slug": "diesel", "icon": "diesel.png"},
    ]

    for t in types:
        if not CarType.query.filter_by(slug=t["slug"]).first():
            db.session.add(CarType(**t, created_at=datetime.utcnow()))

    db.session.commit()
    print("✅ Типы авто добавлены")
