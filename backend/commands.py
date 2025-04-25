from backend.models import db, Category


def init_categories():
    categories = [
        {"name": "New cars", "slug": "new", "icon": "new.png"},
        {"name": "Used cars", "slug": "used", "icon": "used.png"},
        {"name": "Electric", "slug": "electric", "icon": "electric.png"},
        {"name": "Hybrid", "slug": "hybrid", "icon": "hybrid.png"}
    ]

    for cat in categories:
        if not Category.query.filter_by(slug=cat['slug']).first():
            new_cat = Category(**cat)
            db.session.add(new_cat)

    db.session.commit()
