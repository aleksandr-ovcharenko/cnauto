def seed_countries():
    from backend.models import db, Country
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

    for name in countries:
        if not Country.query.filter_by(name=name).first():
            db.session.add(Country(name=name))
    db.session.commit()
    print("✅ Страны успешно добавлены")


if __name__ == "__main__":
    seed_countries()
