# backend/telegram_import.py

import os
from flask import Blueprint, request, jsonify
from backend.models import db, Car, Brand, CarImage
from utils.cloudinary_upload import upload_image

telegram_import = Blueprint('telegram_import', __name__)

@telegram_import.route('/api/import_car', methods=['POST'])
def import_car():
    token = request.form.get("token") or request.headers.get("X-API-TOKEN")
    if token != os.getenv("IMPORT_API_TOKEN"):
        return jsonify({"error": "unauthorized"}), 403

    text = request.form.get("text", "")
    brand_name = request.form.get("brand", "").strip()
    files = request.files.getlist("images")

    if not brand_name or not files:
        return jsonify({"error": "Missing brand or images"}), 400

    # Найдём или создадим бренд
    brand_created = False
    brand = Brand.query.filter_by(name=brand_name).first()
    if not brand:
        brand = Brand(name=brand_name, slug=brand_name.lower().replace(" ", "-"))
        db.session.add(brand)
        db.session.flush()
        brand_created = True

    # Парсим модель и цену
    model = text.split("\n")[0] if text else "Без названия"
    price = 0
    for line in text.split("\n"):
        if any(c in line for c in ["₽", "💵", "цена"]):
            digits = ''.join(filter(str.isdigit, line))
            if digits:
                price = int(digits)
                break

    car = Car(model=model, price=price, brand=brand)
    db.session.add(car)
    db.session.flush()  # получим car.id

    saved_images = []
    for i, file in enumerate(files):
        if file and file.filename:
            url = upload_image(file, car_id=car.id, car_name=car.model, is_main=False, index=i)
            image = CarImage(car_id=car.id, url=url, position=i)
            db.session.add(image)
            saved_images.append(url)

    db.session.commit()

    return jsonify({
        "success": True,
        "car_id": car.id,
        "model": car.model,
        "price": car.price,
        "brand": brand.name,
        "brand_created": brand_created,
        "gallery_images_count": len(saved_images),
        "note": "Главное изображение не установлено — выбери вручную в админке"
    })
