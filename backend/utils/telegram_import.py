import os
import tempfile
import threading
from flask import url_for

import requests
from flask import Blueprint, jsonify, current_app

from backend.models import db, Car, Brand, CarImage, BrandSynonym
from utils.cloudinary_upload import upload_image
from utils.generate_comfyui import generate_with_comfyui
from utils.generator_photon import generate_with_photon
from utils.telegram_file import get_telegram_file_url

REPLICATE_MODE = os.getenv("REPLICATE_MODE", "photon").lower().strip()

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

    # Основные параметры
    model = data.get("model", "").strip()
    price = int(data.get("price", 0) or 0)
    year = int(data.get("year", 0) or 0)
    mileage = int(data.get("mileage", 0) or 0)
    engine = data.get("engine", "").strip()
    car_type_name = data.get("car_type", "").strip()
    brand_name = data.get("brand", "").strip()
    description = data.get("description", "").strip()
    image_file_ids = data.get("image_file_ids", [])

    missing_fields = [field for field in ["model", "brand", "image_file_ids"] if not data.get(field)]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    # Бренд и синоним
    synonym = BrandSynonym.query.filter(BrandSynonym.name.ilike(brand_name)).first()
    brand = synonym.brand if synonym else None

    brand_created = False
    if not brand:
        brand = Brand(name=brand_name, slug=brand_name.lower().replace(" ", "-"))
        db.session.add(brand)
        db.session.flush()

        synonym = BrandSynonym(name=brand_name.lower(), brand=brand)
        db.session.add(synonym)
        db.session.flush()
        brand_created = True

    # Тип кузова
    car_type = None
    if car_type_name:
        car_type = CarType.query.filter_by(name=car_type_name).first()
        if not car_type:
            car_type = CarType(name=car_type_name, slug=car_type_name.lower().replace(" ", "-"))
            db.session.add(car_type)
            db.session.flush()

    # Создание авто
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

    # Промпт
    prompt_hint = (
        "Professional car studio shot, clean background, only the car visible. "
        f"Car: {brand.name} {model}, fully isolated, no other objects or cars. "
        "License plate must clearly show 'cncars.ru'. "
        "Car positioned diagonally: front facing left, rear facing right. "
        "Clean, sharp details, high-quality render, studio lighting. "
        "Remove all background elements, shadows, and distractions. "
        "The car should look like a perfect 3D model on a white background."
    )

    # Обработка изображений
    real_urls = []
    main_image_url = None

    if image_file_ids:
        try:
            # Первое изображение - главное
            first_file_id = image_file_ids[0]
            url = get_telegram_file_url(first_file_id)
            main_image_url = download_and_reupload(url, car_id=car.id, car_name=car.model, is_main_img=True)
            if main_image_url:
                car.image_url = main_image_url
                db.session.commit()
                # Создаем копии всех данных, которые понадобятся в потоке
                thread_data = {
                    'app': current_app._get_current_object(),
                    'prompt': prompt_hint,
                    'image_url': main_image_url,
                    'car_model': model,
                    'brand_name': brand.name,
                    'car_id': car.id
                }
                thread = threading.Thread(target=async_generate_image, kwargs=thread_data)
                thread.start()
                print(f"✅ Загружено главное изображение: {main_image_url}")

                                # Остальные изображения - галерея
                for i, file_id in enumerate(image_file_ids[1:], start=1):  # Начинаем с 1, так как 0 - главное изображение
                    try:
                        url = get_telegram_file_url(file_id)
                        ref_url = download_and_reupload(
                            url,
                            car_id=car.id,
                            car_name=car.model,
                            is_main_img=False,
                            image_index=i  # Передаем индекс изображения
                        )
                        if ref_url:
                            real_urls.append(ref_url)
                    except Exception as e:
                        print(f"⚠️ Ошибка при обработке изображения галереи (индекс {i}): {e}")


        except Exception as e:
            print(f"⚠️ Ошибка при обработке главного изображения: {e}")

    # Добавляем изображения галереи
    for i, url in enumerate(real_urls):
        image = CarImage(car_id=car.id, url=url, position=i)
        db.session.add(image)

    db.session.commit()

    # Генерация URL для просмотра автомобиля
    car_url = f"http://{os.getenv('SERVER_NAME', 'localhost:5000')}{url_for('car_page', car_id=car.id)}"
    admin_car_edit_url = f"http://{os.getenv('SERVER_NAME', 'localhost:5000')}" + url_for('car.edit_view', id=car.id, url='/admin/car/')

    print(f"⚠️ Ссылка на сайт: {car_url}")
    print(f"⚠️ Редактировать в админке: {admin_car_edit_url}")

    # Добавляем в JSON-ответ
    return jsonify({
        "success": True,
        "car_id": car.id,
        "model": car.model,
        "price": car.price,
        "year": car.year,
        "brand": brand.name,
        "brand_created": brand_created,
        "main_image": main_image_url,
        "gallery_images_count": len(real_urls),
        "prompt_hint": prompt_hint,
        "car_url": car_url,
        "admin_edit_url": admin_car_edit_url
    })


def async_generate_image(app, prompt, image_url, car_model, brand_name, car_id):
    with app.app_context():
        try:
            # Получаем бренд заново в контексте потока
            brand = Brand.query.filter_by(name=brand_name).first()

            ai_image = generate_image(
                mode="photon",
                prompt=prompt,
                image_url=image_url,
                car_model=car_model,
                car_brand=brand,
                car_id=car_id
            )
            if ai_image:
                car = Car.query.get(car_id)
                if car:
                    car.image_url = ai_image
                    db.session.commit()
                    print(f"✅ Сгенерировано AI изображение: {ai_image}")
        except Exception as e:
            print("⚠️ Не удалось сгенерировать главное изображение.")
            print("📝 Prompt:", prompt)
            print("💥 Ошибка:", e)


def download_and_reupload(url: str, car_id=None, car_name=None, is_main_img=False, image_index=None) -> str:
    try:
        print(f"⬇️ Скачиваем изображение {image_index} с {url}")
        response = requests.get(url)
        response.raise_for_status()

        # Определяем расширение файла
        file_ext = os.path.splitext(url.split('?')[0])[1] or '.jpg'

        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        print(f"☁️ Загружаем изображение {image_index} в Cloudinary...")
        uploaded_url = upload_image(
            tmp_path,
            car_id=car_id,
            car_name=car_name,
            is_main=is_main_img,
            index=image_index  # Передаем индекс в upload_image
        )

        # Удаляем временный файл
        try:
            os.unlink(tmp_path)
        except Exception as e:
            print(f"⚠️ Не удалось удалить временный файл: {e}")

        return uploaded_url
    except Exception as e:
        print(f"❌ Ошибка при обработке изображения {image_index}: {e}")
        return None


def generate_image(mode: str = None, prompt: str = "", image_url: str = "", car_model: str = "", car_brand=None,
                   car_id=None) -> str:
    mode = (mode or REPLICATE_MODE).lower().strip()
    print(f"🚀 Генерация изображение [mode={mode}]")

    ref_url = download_and_reupload(image_url, car_id=car_id, car_name=car_model, is_main_img=True)
    if not ref_url:
        print("⚠️ Прерывание: не удалось загрузить изображение в Cloudinary")
        return None

    if mode == "photon":
        return generate_with_photon(prompt, ref_url, car_model, car_brand, car_id)
    elif mode == "comfy":
        return generate_with_comfyui(ref_url, prompt, car_model, car_brand, car_id)
    else:
        raise ValueError(f"❌ Неизвестный режим генерации: {mode}")
