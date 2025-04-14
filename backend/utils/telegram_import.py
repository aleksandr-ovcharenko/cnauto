# backend/telegram_import.py

import os

from flask import Blueprint, jsonify

from backend.models import db, Car, Brand, CarImage
from utils.telegram_file import get_telegram_file_url

telegram_import = Blueprint('telegram_import', __name__)


@telegram_import.route('/api/import_car', methods=['POST'])
def import_car(request):
    from backend.models import CarType

    token = request.headers.get("X-API-TOKEN")
    if token != os.getenv("IMPORT_API_TOKEN"):
        return jsonify({"error": "unauthorized"}), 403

    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "invalid json"}), 400

    model = data.get("model", "").strip()
    price = int(data.get("price", 0) or 0)
    year = int(data.get("year", 0) or 0)
    mileage = int(data.get("mileage", 0) or 0)
    engine = data.get("engine", "").strip()
    car_type_name = data.get("car_type", "").strip()
    brand_name = data.get("brand", "").strip()
    description = data.get("description", "").strip()
    image_file_ids = data.get("image_file_ids", [])

    missing_fields = []
    if not model:
        missing_fields.append("model")
    if not brand_name:
        missing_fields.append("brand")
    if not image_file_ids:
        missing_fields.append("image_file_ids")

    if missing_fields:
        return jsonify({
            "error": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400

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
        year=year,
        mileage=mileage,
        engine=engine,
        brand=brand,
        car_type=car_type,
        description=description,
    )
    db.session.add(car)
    db.session.flush()

    # Получим реальные URL из file_ids
    real_urls = []
    for file_id in image_file_ids:
        try:
            url = get_telegram_file_url(file_id)
            real_urls.append(url)

        except Exception as e:
            print(f"⚠️ Ошибка при получении URL из Telegram: {e}")

    # Сохраняем изображения
    for i, url in enumerate(real_urls):
        image = CarImage(car_id=car.id, url=url, position=i)
        db.session.add(image)

    db.session.commit()

    print(
        f"✅ Создан автомобиль: {car.model} ({car.price} ₽) — {brand.name} | "
        f"ID: {car.id} | Фото: {len(real_urls)}"
    )

    # Генерация главной картинки из первой
    ai_image = None
    prompt_hint = None

    try:
        from utils.replicate_api import generate_main_image
        ai_image = generate_main_image(real_urls[0], car_model=model, car_brand=brand)
        if ai_image:
            car.image_url = ai_image
            print(f"✅ Сгенерировано AI изображение: {ai_image}")
    except Exception as e:
        prompt_hint = (
            f"Очисти это фото, чтобы модель {model} стояла одна, "
            "на номере напиши cnauto.ru, поверни мордой влево и вперед, "
            "зад направь вправо и назад, по диагонали."
        )
        print("⚠️ Не удалось сгенерировать главное изображение.")
        print("📝 Prompt:", prompt_hint)
        print("💥 Ошибка:", e)

    return jsonify({
        "success": True,
        "car_id": car.id,
        "model": car.model,
        "price": car.price,
        "year": year,
        "brand": brand.name,
        "brand_created": brand_created,
        "main_image": ai_image,
        "gallery_images_count": len(real_urls),
        "prompt_hint": prompt_hint if not ai_image else None
    })
