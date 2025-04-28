import os
# Use relative imports
import sys
import tempfile

import requests
from flask import Blueprint, jsonify, current_app, request, url_for

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import db, Car, Brand, CarImage, BrandSynonym, Currency
from utils.cloudinary_upload import upload_image
from utils.generate_comfyui import generate_with_comfyui
from utils.generator_photon import generate_with_photon
from utils.telegram_file import get_telegram_file_url
from utils.file_logger import get_module_logger
from utils.image_queue import enqueue_image_task
from utils.car_parser import parse_car_info, save_new_trims_to_db

# Configure logging using the centralized logger
logger = get_module_logger(__name__)

REPLICATE_MODE = os.getenv("REPLICATE_MODE", "photon").lower().strip()
telegram_import = Blueprint('telegram_import', __name__)

# Store a reference to the Flask app - will be set when the blueprint is registered
_app = None


def get_app_context():
    """Get the app context safely, either from current_app or stored _app reference"""
    global _app
    try:
        # Try to use current_app first (in request context)
        return current_app.app_context()
    except RuntimeError:
        # If no request context, use stored app reference
        if _app is not None:
            return _app.app_context()
        else:
            # This should only happen during testing or if not properly initialized
            logger.error("❌ No Flask app context available and no stored app reference")
            raise RuntimeError("No Flask app context available")


@telegram_import.record
def record_app(state):
    """Store a reference to the Flask app when the blueprint is registered"""
    global _app
    _app = state.app
    logger.info("✅ Stored Flask app reference for background processing")


@telegram_import.route('/api/import_car', methods=['POST'])
def import_car():
    from models import CarType

    logger.info("🚗 Started importing car via API")

    token = request.headers.get("X-API-TOKEN")
    logger.debug(f"Received token: {token}")
    logger.debug(f"Expected token: {os.getenv('IMPORT_API_TOKEN')}")
    if token != os.getenv("IMPORT_API_TOKEN"):
        return jsonify({"error": "unauthorized, check your token"}), 403

    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "invalid json"}), 400

    car_data_str = data.get("car_data", "").strip()
    # Process car data if in the new format [Brand] [Model] [Modification]
    if car_data_str:
        logger.info(f"🚗 Processing car in new format: {car_data_str}")
        # Parse car data into bmmt format using the current db session
        car_info = parse_car_info(car_data_str, db_session=db.session)
        # Update data with parsed values
        data["brand"] = car_info["brand"]
        data["model"] = car_info["model"]
        data["modification"] = car_info["modification"]
        data["trim"] = car_info["trim"]

    model = data.get("model", "").strip()
    modification = data.get("modification", "").strip()
    trim = data.get("trim", "").strip()
    price = int(data.get("price", 0) or 0)
    year = int(data.get("year", 0) or 0)
    mileage = int(data.get("mileage", 0) or 0)
    engine = data.get("engine", "").strip()
    car_type_name = data.get("car_type", "").strip()
    brand_name = data.get("brand", "").strip()
    description = data.get("description", "").strip()
    image_file_ids = data.get("image_file_ids", [])

    # Validation: block car creation without brand and model
    if not brand_name or not model:
        return jsonify({"error": "Нельзя создать автомобиль без бренда и модели."}), 400

    missing_fields = [field for field in ["model", "brand", "image_file_ids"] if not data.get(field)]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    synonym = BrandSynonym.query.filter(BrandSynonym.name.ilike(brand_name)).first()
    brand = synonym.brand if synonym else None

    brand_created = False
    if not brand:
        # Check if a brand with this slug already exists (case insensitive)
        slug = brand_name.lower().replace(" ", "-")
        existing_brand = Brand.query.filter(Brand.slug == slug).first()

        if existing_brand:
            # Use the existing brand instead of creating a new one
            brand = existing_brand
            logger.info(f"✅ Using existing brand: {brand.name} (slug: {brand.slug})")
        else:
            # Create a new brand only if it doesn't exist
            brand = Brand(name=brand_name, slug=slug)
            db.session.add(brand)
            db.session.flush()

            synonym = BrandSynonym(name=brand_name.lower(), brand=brand)
            db.session.add(synonym)
            db.session.flush()
            brand_created = True
            logger.info(f"✅ Created new brand: {brand.name} (slug: {brand.slug})")

    car_type = None
    if car_type_name:
        car_type = CarType.query.filter_by(name=car_type_name).first()
        if not car_type:
            car_type = CarType(name=car_type_name, slug=car_type_name.lower().replace(" ", "-"))
            db.session.add(car_type)
            db.session.flush()

    currency_code = data.get("currency")
    currency = None
    if currency_code:
        currency = Currency.query.filter_by(code=currency_code).first()
        if not currency:
            logger.warning(f"⚠️ Currency with code '{currency_code}' not found. Defaulting to None.")

    car = Car(
        model=model,
        modification=modification,
        trim=trim,
        price=price,
        year=year,
        mileage=mileage,
        engine=engine,
        brand=brand,
        car_type=car_type,
        description=description,
        currency=currency,
    )
    db.session.add(car)
    db.session.flush()

    # If we had new trims identified during parsing, save them to the database
    if 'car_data' in data:
        save_new_trims_to_db(db_session=db.session)

    prompt_hint = (
        "Professional car studio shot, ultra-clean pure white background, only the car visible with ample empty space around it. "
        f"Car: {car.model}-{car.brand.name}, perfectly isolated with at least 2 meters of empty space on all sides, no other objects or cars visible. "
        "License plate must clearly and legibly display 'cncars.ru' in proper format. "
        "Car positioned diagonally in frame: front facing 30 degrees left, rear facing 30 degrees right, with slight perspective as if viewed from eye level. "
        "The car should be positioned not too close - about 5-7 meters from the virtual camera, showing full body with space around. "
        "Crisp, ultra-sharp details, 8K quality render, professional three-point studio lighting with soft shadows. "
        "Absolutely no background elements, no reflections of surroundings, no stray shadows - only clean, pure white backdrop. "
        "The car should appear as a flawless 3D model with perfect proportions, slightly matte surface to avoid glare. "
        "Add subtle ambient occlusion shadows under the car for natural grounding effect."
    )

    real_urls = []
    main_image_url = None

    if image_file_ids:
        try:
            first_file_id = image_file_ids[0]
            url = get_telegram_file_url(first_file_id)
            main_image_url = download_and_reupload(url, car_id=car.id, car_name=car.model, is_main_img=True)
            if main_image_url:
                car.image_url = main_image_url
                db.session.commit()

                params = {
                    'mode': REPLICATE_MODE,
                    'prompt': prompt_hint,
                    'image_url': main_image_url,
                    'car_model': model,
                    'car_brand': brand,
                    'car_id': car.id
                }

                # Enqueue the task with our new queuing system
                task_id = enqueue_image_task(
                    car_id=car.id,
                    generator_func=generate_image,  # This is our local function
                    params=params,
                    max_retries=3
                )
                logger.info(f"🎯 Queued AI image generation as task: {task_id}")

                for i, file_id in enumerate(image_file_ids[1:], start=1):
                    try:
                        url = get_telegram_file_url(file_id)
                        ref_url = download_and_reupload(
                            url,
                            car_id=car.id,
                            car_name=car.model,
                            is_main_img=False,
                            image_index=i
                        )
                        if ref_url:
                            real_urls.append(ref_url)
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка при обработке изображения галереи (индекс {i}): {e}")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при обработке главного изображения: {e}")

    # Add real image URLs to the Car's gallery
    for i, url in enumerate(real_urls):
        image = CarImage(car_id=car.id, url=url, position=i)
        db.session.add(image)

    db.session.commit()

    # Get the admin edit URL for the car
    admin_car_edit_url = f"/admin/car/edit/?id={car.id}"

    car_url = f"http://{os.getenv('SERVER_NAME', 'localhost:5000')}{url_for('car_page', car_id=car.id)}"
    admin_car_edit_url = f"http://{os.getenv('SERVER_NAME', 'localhost:5000')}/admin/car/edit/?id={car.id}&url=/admin/car/"

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
    """
    Legacy function maintained for backward compatibility.
    New code should use the image_queue system instead.
    """
    with app.app_context():
        try:
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
                    logger.info(f"✅ Сгенерировано AI изображение: {ai_image}")
        except Exception as e:
            logger.exception("⚠️ Не удалось сгенерировать главное изображение")


def download_and_reupload(url: str, car_id=None, car_name=None, is_main_img=False, image_index=None) -> str:
    try:
        logger.info(f"⬇️ Скачиваем изображение {image_index} с {url}")
        response = requests.get(url)
        response.raise_for_status()

        file_ext = os.path.splitext(url.split('?')[0])[1] or '.jpg'

        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        logger.info(f"☁️ Загружаем изображение {image_index} в Cloudinary...")
        uploaded_url = upload_image(
            tmp_path,
            car_id=car_id,
            car_name=car_name,
            is_main=is_main_img,
            index=image_index
        )

        try:
            os.unlink(tmp_path)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось удалить временный файл: {e}")

        return uploaded_url
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке изображения {image_index}: {e}")
        return None


def generate_image(mode: str = None, prompt: str = "", image_url: str = "", car_model: str = "", car_brand=None,
                   car_id=None) -> str:
    """Generate an AI image using the specified mode and parameters"""
    mode = (mode or REPLICATE_MODE).lower().strip()
    logger.info(f"🚀 Генерация изображение [mode={mode}]")

    # Use app context to ensure current_app is available in background threads
    with get_app_context():
        ref_url = download_and_reupload(image_url, car_id=car_id, car_name=car_model, is_main_img=True)
        if not ref_url:
            logger.warning("⚠️ Прерывание: не удалось загрузить изображение в Cloudinary")
            return None

        if mode == "photon":
            return generate_with_photon(prompt, ref_url, car_model, car_brand, car_id)
        elif mode == "comfy":
            return generate_with_comfyui(prompt, ref_url, car_model, car_brand, car_id)
        else:
            logger.warning(f"⚠️ Неизвестный режим генерации: {mode}")
            return None
