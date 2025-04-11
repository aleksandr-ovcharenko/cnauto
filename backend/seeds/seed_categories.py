from backend.models import db, Category
from backend.app import app
from datetime import datetime

with app.app_context():
    categories = [
        {"name": "Седан", "slug": "sedan", "icon": "sedan.png"},
        {"name": "Кроссовер", "slug": "crossover", "icon": "crossover.png"},
        {"name": "Минивэн", "slug": "minivan", "icon": "minivan.png"},
        {"name": "Пикап", "slug": "pickup", "icon": "pickup.png"},
        {"name": "Хэтчбек", "slug": "hatchback", "icon": "hatchback.png"},
    ]

    for c in categories:
        if not Category.query.filter_by(slug=c["slug"]).first():
            db.session.add(Category(**c, created_at=datetime.utcnow()))

    db.session.commit()
    print("✅ Категории добавлены")
