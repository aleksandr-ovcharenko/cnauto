import os
import sys
import tempfile
import threading
from functools import partial

# Add parent directory to path for consistent imports
# This ensures the module can be run directly or imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import requests
from flask import Blueprint, jsonify, current_app, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Use try-except pattern for imports to support both package and direct imports
try:
    from backend.models import db, Car, Brand, CarImage, BrandSynonym, Currency, CarType
except ImportError:
    from models import db, Car, Brand, CarImage, BrandSynonym, Currency, CarType

try:
    from backend.utils.cloudinary_upload import upload_image
except ImportError:
    from utils.cloudinary_upload import upload_image

try:
    from backend.utils.generate_comfyui import generate_with_comfyui
except ImportError:
    from utils.generate_comfyui import generate_with_comfyui

try:
    from backend.utils.generator_photon import generate_with_photon
except ImportError:
    from utils.generator_photon import generate_with_photon

try:
    from backend.utils.telegram_file import get_telegram_file_url
except ImportError:
    from utils.telegram_file import get_telegram_file_url

try:
    from backend.utils.file_logger import get_module_logger
except ImportError:
    from utils.file_logger import get_module_logger

try:
    from backend.utils.image_queue import enqueue_image_task
except ImportError:
    from utils.image_queue import enqueue_image_task

try:
    from backend.utils.car_parser import parse_car_info, save_new_trims_to_db
except ImportError:
    from utils.car_parser import parse_car_info, save_new_trims_to_db

# Configure logging using the centralized logger
logger = get_module_logger(__name__)

REPLICATE_MODE = os.getenv("REPLICATE_MODE", "photon").lower().strip()
telegram_import = Blueprint('telegram_import', __name__)

# Store a reference to the Flask app - will be set when the blueprint is registered
_app = None
_db_session = None


def get_db_session(app=None):
    """Get a direct SQLAlchemy session without relying on Flask-SQLAlchemy"""
    global _db_session

    if _db_session is not None:
        return _db_session

    try:
        # Try to get the database URL from the app config
        if app is not None:
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        else:
            try:
                db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
            except RuntimeError:
                # Use environment variable as fallback for Railway
                db_uri = os.getenv('DATABASE_URL')

        if not db_uri:
            logger.error("❌ Database URI not found in app config or environment")
            raise RuntimeError("Database URI not available")

        # Create direct SQLAlchemy engine and session
        engine = create_engine(db_uri)
        session_factory = sessionmaker(bind=engine)
        _db_session = scoped_session(session_factory)
        return _db_session
    except Exception as e:
        logger.error(f"❌ Error creating database session: {e}")
        raise


def get_app_context(app=None):
    """Get the app context safely, either from current_app or stored _app reference"""
    try:
        # Try to use current_app first (in request context)
        return current_app.app_context()
    except RuntimeError:
        # If no request context, use stored app reference
        if app is not None:
            return app.app_context()
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


# Helper to send a Telegram message
def send_telegram_message(chat_id, text, bot_token=None):
    import requests
    if not bot_token:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN is not set!")
        return False
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info(f"✅ Sent Telegram message to {chat_id}")
            return True
        else:
            logger.error(f"❌ Failed to send Telegram message: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Exception in send_telegram_message: {e}")
        return False


# Extracted car import logic for async processing
def process_car_import_task(app, data, chat_id):
    session = None
    try:
        session = get_db_session(app=app)
        car_data_str = data.get("car_data", "").strip()
        if car_data_str:
            logger.info(f"🚗 Processing car in new format: {car_data_str}")
            car_info = parse_car_info(car_data_str, db_session=session)
            data["brand"] = car_info["brand"]
            data["model"] = car_info["model"]
            data["modification"] = car_info["modification"]
            data["trim"] = car_info["trim"]
            logger.info(
                f"✅ Parsed car data: Brand={car_info['brand']}, Model={car_info['model']}, Modification={car_info['modification']}, Trim={car_info['trim']}")
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
        missing_fields = [field for field in ["model", "brand", "image_file_ids"] if not data.get(field)]
        if missing_fields:
            send_telegram_message(chat_id, f"❌ Ошибка: отсутствуют обязательные поля: {', '.join(missing_fields)}")
            return
        synonym = session.query(BrandSynonym).filter(BrandSynonym.name.ilike(brand_name)).first()
        brand = synonym.brand if synonym else None
        brand_created = False
        if not brand:
            slug = brand_name.lower().replace(" ", "-")
            existing_brand = session.query(Brand).filter(Brand.slug == slug).first()
            if existing_brand:
                brand = existing_brand
                logger.info(f"✅ Using existing brand: {brand.name} (slug: {brand.slug})")
            else:
                brand = Brand(name=brand_name, slug=slug)
                session.add(brand)
                session.flush()
                synonym = BrandSynonym(name=brand_name.lower(), brand=brand)
                session.add(synonym)
                session.flush()
                brand_created = True
                logger.info(f"✅ Created new brand: {brand.name} (slug: {brand.slug})")
        car_type = None
        if car_type_name:
            car_type = session.query(CarType).filter_by(name=car_type_name).first()
            if not car_type:
                car_type = CarType(name=car_type_name, slug=car_type_name.lower().replace(" ", "-"))
                session.add(car_type)
                session.flush()
        currency_code = data.get("currency")
        currency = None
        if currency_code:
            currency = session.query(Currency).filter_by(code=currency_code).first()
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
        session.add(car)
        session.flush()
        prompt_hint = (
            "Professional car studio shot, ultra-clean pure white background, only the car visible with ample empty space around it. "
            f"Car: {car.brand.name if car.brand else 'Unknown'} {car.model}, perfectly isolated with at least 2 meters of empty space on all sides, no other objects or cars visible. "
            "License plate must clearly and legibly display 'cncars.ru' in proper format. "
            f"Car positioned diagonally in frame: front facing 30 degrees left, rear facing 30 degrees right, with slight perspective as if viewed from eye level. "
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
                main_image_url = download_and_reupload(url, car_id=car.id, car_name=car.model, car_brand=car.brand.name, is_main_img=True, app=app)
                if main_image_url:
                    car.image_url = main_image_url
                    session.commit()
                    params = {
                        'mode': REPLICATE_MODE,
                        'prompt': prompt_hint,
                        'image_url': main_image_url,
                        'car_model': model,
                        'car_brand': brand.name if brand else "Unknown",  
                        'car_id': car.id,
                        'app': app
                    }
                    task_id = enqueue_image_task(
                        car_id=car.id,
                        generator_func=generate_image,
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
                                car_brand=car.brand.name,
                                is_main_img=False,
                                image_index=i,
                                app=app
                            )
                            if ref_url:
                                real_urls.append(ref_url)
                        except Exception as e:
                            logger.warning(f"⚠️ Ошибка при обработке изображения галереи (индекс {i}): {e}")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при обработке главного изображения: {e}")
        for i, url in enumerate(real_urls):
            image = CarImage(car_id=car.id, url=url, position=i)
            session.add(image)
        session.commit()

        # Compose detailed message
        details = [
            "✅ Автомобиль успешно добавлен!",
            "",
            "Распознано:",
            f"• Бренд: {brand_name or 'не указано'}",
            f"• Модель: {model or 'не указано'}",
            f"• Модификация: {modification or 'не указано'}" if modification else None,
            f"• Комплектация: {trim or 'не указано'}" if trim else None,
            f"• Год: {year or 'не указано'}" if year else None,
            f"• Пробег: {mileage} км" if mileage is not None else None,
            f"• Двигатель: {engine or 'не указано'}" if engine else None,
            f"• Тип: {car_type_name or 'не указано'}" if car_type_name else None,
            f"• Цена: {price:,} {currency_code or ''}" if price else None,
            ""
        ]
        if description:
            details.append(f"Описание: {description}")
            details.append("")
        if main_image_url:
            details.append("Главное изображение:")
            details.append(main_image_url)
        
        # Initialize URL variables early
        car_url = None
        admin_car_edit_url = None
        
        # Build URLs directly without relying on url_for
        try:
            # Get server name from environment or use default
            server_name = os.getenv('SERVER_NAME')
            # If SERVER_NAME is not set, check if we have RAILWAY_PUBLIC_DOMAIN
            if not server_name:
                server_name = os.getenv('RAILWAY_PUBLIC_DOMAIN')
            # If still no domain, use default
            if not server_name:
                server_name = "cncars.ru"
                
            # Build the URLs directly
            car_url = f"https://{server_name}/car/{car.id}"
            admin_car_edit_url = f"https://{server_name}/admin/car/edit/?id={car.id}&url=/admin/car/"
            logger.info(f"✅ Generated car URLs using server: {server_name}")
        except Exception as e:
            logger.error(f"❌ Error generating car URLs: {e}")
            
        # Improved gallery output
        max_gallery_preview = 2
        if real_urls:
            details.append(f"Галерея: {len(real_urls)} фото" + (
                f" (первые {max_gallery_preview}):" if len(real_urls) > max_gallery_preview else ":"))
            for url in real_urls[:max_gallery_preview]:
                details.append(url)
            if len(real_urls) > max_gallery_preview:
                details.append(f"и еще {len(real_urls) - max_gallery_preview} фото — см. все на сайте:")
                if car_url:
                    details.append(car_url)
        # If new trims were added
        new_trims = []
        if 'car_data' in data:
            new_trims = save_new_trims_to_db(db_session=session) or []
        if new_trims:
            details.append("")
            details.append(
                "Новые комплектации/модификации, добавленные в базу: " + ", ".join(str(t) for t in new_trims))
            
        # Place links at the end, clearly labeled
        if car_url:
            details.append("")
            details.append(f"Ссылка на авто на сайте:\n{car_url}")
        if admin_car_edit_url:
            details.append(f"Ссылка для администрирования:\n{admin_car_edit_url}")
        msg = "\n".join([d for d in details if d])
        send_telegram_message(chat_id, msg)
    except Exception as e:
        logger.error(f"❌ Ошибка при импорте автомобиля: {e}")
        if chat_id:
            send_telegram_message(chat_id, f"❌ Ошибка при импорте автомобиля: {e}")
    finally:
        if session:
            session.close()


@telegram_import.route('/api/import_car', methods=['POST'])
def import_car():
    logger.info("🚗 Started importing car via API [ASYNC]")
    token = request.headers.get("X-API-TOKEN")
    if token != os.getenv("IMPORT_API_TOKEN"):
        return jsonify({"error": "unauthorized, check your token"}), 403
    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "invalid json"}), 400
    chat_id = data.get("chat_id")
    if not chat_id:
        return jsonify({"error": "chat_id required in payload"}), 400
    app = current_app._get_current_object()
    threading.Thread(target=partial(process_car_import_task, app), args=(data, chat_id), daemon=True).start()
    return jsonify({"status": "received", "message": "Работаем над вашей заявкой..."})

def download_and_reupload(url: str, car_id=None, car_name=None, car_brand=None, is_main_img=False, image_index=None, app=None) -> str:
    try:
        logger.info(f"⬇️ Скачиваем изображение {image_index} с {url}")
        response = requests.get(url)
        response.raise_for_status()
        file_ext = os.path.splitext(url.split('?')[0])[1] or '.jpg'
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
        
        logger.info(f"☁️ Загружаем изображение {image_index} в Cloudinary...")
        
        # Use Flask application context to ensure correct Cloudinary folder is used
        with get_app_context(app=app):
            uploaded_url = upload_image(
                tmp_path,
                car_id=car_id,
                car_name=car_name,
                car_brand=car_brand,
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
                   car_id=None, app=None) -> str:
    mode = (mode or REPLICATE_MODE).lower().strip()
    logger.info(f"🚀 Генерация изображение [mode={mode}]")
    with get_app_context(app=app):
        ref_url = download_and_reupload(
            image_url, 
            car_id=car_id, 
            car_name=car_model, 
            car_brand=car_brand,  
            is_main_img=True, 
            app=app
        )
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
