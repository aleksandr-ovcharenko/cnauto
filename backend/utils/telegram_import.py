# backend/telegram_import.py

import os
from flask import Blueprint, request, jsonify
from backend.models import db, Car, Brand, CarImage
from utils.cloudinary_upload import upload_image

telegram_import = Blueprint('telegram_import', __name__)

@telegram_import.route('/api/import_car', methods=['POST'])
def import_car(request):
    import json
    from backend.models import CarType

    token = request.headers.get("X-API-TOKEN")
    if token != os.getenv("IMPORT_API_TOKEN"):
        return jsonify({"error": "unauthorized"}), 403

    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "invalid json"}), 400

    model = data.get("model", "").strip()
    price = int(data.get("price", 0))
    mileage = data.get("mileage")
    engine = data.get("engine", "")
    car_type_name = data.get("car_type", "")
    brand_name = data.get("brand", "").strip()
    description = data.get("description", "")
    image_urls = data.get("image_urls", [])

    if not model or not brand_name or not image_urls:
        return jsonify({"error": "Missing required fields"}), 400

    # Найдём или создадим бренд
    brand_created = False
    brand = Brand.query.filter_by(name=brand_name).first()
    if not brand:
        brand = Brand(name=brand_name, slug=brand_name.lower().replace(" ", "-"))
        db.session.add(brand)
        db.session.flush()
        brand_created = True

    # Найдём или создадим тип кузова
    car_type = None
    if car_type_name:
        car_type = CarType.query.filter_by(name=car_type_name).first()
        if not car_type:
            car_type = CarType(name=car_type_name, slug=car_type_name.lower().replace(" ", "-"))
            db.session.add(car_type)
            db.session.flush()

    # Создаём авто
    car = Car(
        model=model,
        price=price,
        mileage=mileage,
        engine=engine,
        brand=brand,
        car_type=car_type,
        description=description,
    )
    db.session.add(car)
    db.session.flush()

    # Сохраняем изображения
    for i, url in enumerate(image_urls):
        image = CarImage(car_id=car.id, url=url, position=i)
        db.session.add(image)

    db.session.commit()

    return jsonify({
        "success": True,
        "car_id": car.id,
        "model": car.model,
        "price": car.price,
        "brand": brand.name,
        "brand_created": brand_created,
        "gallery_images_count": len(image_urls),
        "note": "Please add main picture in admin view"
    })