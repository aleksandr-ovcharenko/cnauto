from backend.models import db, Country
from backend.app import app

def seed_countries():
    countries = [
        "Китай",
        "Германия",
        "Япония",
        "Корея",
        "США",
        "Франция",
        "Швеция",
        "Чехия",
        "Англия"
    ]

    with app.app_context():
        for name in countries:
            if not Country.query.filter_by(name=name).first():
                db.session.add(Country(name=name))
        db.session.commit()
        print("✅ Страны успешно добавлены")

if __name__ == "__main__":
    seed_countries()
