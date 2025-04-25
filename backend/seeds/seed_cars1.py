import logging

from backend.models import db, Car, Brand, CarType


def seed_cars():
    cars_data = [
        {
            "model": "GLC 300 L 4MATIC Luxury",
            "price": 33700,
            "brand": "mercedes",
            "car_type_name": "Гибрид",
            "year": 2022,
            "mileage": 35000,
            "engine": "2.0T (турбо), 258 л.с.",
            "description": "Отличное состояние, система полного привода (4MATIC)",
            "image": "mercedes-glc-300.jpg"
        },
        {
            "model": "GLE 450 4MATIC Dynamic",
            "price": 65600,
            "brand": "mercedes",
            "car_type_name": "Гибрид",
            "year": 2024,
            "mileage": 9000,
            "engine": "2.5T (турбо), 367 л.с.",
            "description": "Оригинальная краска, переднемоторная компоновка с полным приводом",
            "image": "mercedes-gle-450.jpg"
        },
        {
            "model": "BYD Han EV Flagship",
            "price": 28900,
            "brand": "byd",
            "car_type_name": "Электро",
            "year": 2023,
            "mileage": 12000,
            "engine": "Электродвигатель, 510 л.с.",
            "description": "Полный привод, топовая комплектация",
            "image": "byd-han.jpg"
        }
    ]

    for data in cars_data:
        brand = Brand.query.filter_by(slug=data["brand"]).first()
        car_type = CarType.query.filter_by(name=data["car_type_name"]).first()

        if not brand or not car_type:
            print(f"❌ Пропущено: {data['model']} (нет бренда или типа)")
            logging.getLogger(__name__).warning(f"❌ Пропущено: {data['model']} (нет бренда или типа)")
            continue

        car = Car(
            model=data["model"],
            price=data["price"],
            image=data["image"],
            description=data["description"],
            in_stock=True,
            brand=brand,
            car_type=car_type,
            year=data["year"],
            mileage=data["mileage"],
            engine=data["engine"],
        )
        db.session.add(car)

    db.session.commit()
    print("✅ Машины успешно добавлены.")
    logging.getLogger(__name__).info("✅ Машины успешно добавлены.")


if __name__ == "__main__":
    from backend.app import app

    with app.app_context():
        seed_cars()
