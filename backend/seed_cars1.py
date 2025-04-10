from backend.app import app
from backend.models import db, Car

cars = [
    {
        "model": "Рестайлинг GLC 300 L 4MATIC Luxury",
        "price": 33700,
        "year": "Июнь 2022 года",
        "mileage": "35 000 км",
        "engine": "2.0T (турбо), 258 л.с., полный привод (4WD)",
        "extras": "Отличное состояние, система полного привода (4MATIC)",
        "price_fob": "$33 700 долларов США",
        "brand_slug": "mercedes",
        "image": "glc300.webp"
    },
    {
        "model": "Рестайлинг GLE 450 4MATIC Dynamic",
        "price": 65600,
        "year": "Сентябрь 2024 года",
        "mileage": "9 000 км",
        "engine": "2.5T (турбо), 367 л.с., полный привод (4WD)",
        "extras": "Оригинальная краска, переднемоторная компоновка с полным приводом",
        "price_fob": "$65 600 долларов США",
        "brand_slug": "mercedes",
        "image": "gle450.webp"
    }
]

with app.app_context():
    for car_data in cars:
        car = Car.query.filter_by(model=car_data['model']).first()
        if not car:
            car = Car(**car_data)
            db.session.add(car)
    db.session.commit()
    print("✅ Автомобили добавлены")
