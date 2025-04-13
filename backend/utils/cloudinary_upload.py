import cloudinary.uploader
from flask import current_app


def upload_image(file, car_id=None, car_name=None, is_main=False, index=None):
    base_folder = current_app.config.get("CLOUDINARY_FOLDER", "cn-auto/misc")
    base_name = f"{car_name or 'car'}_{'main' if is_main else f'gallery_{index}'}".lower().replace(" ", "_")
    # Путь: <окружение>/cars/<id>/
    car_folder = f"{base_folder}/cars/{car_id or 'unknown'} - {car_name or 'unknown'}"
    print(f"📂 Загрузка в Cloudinary → Папка: {car_folder} | Файл: {base_name}")

    try:
        result = cloudinary.uploader.upload(
            file,
            folder=car_folder,  # создаёт физическую папку
            public_id=base_name,  # только имя файла
            overwrite=True,
            resource_type="image",
            use_filename=False,
            unique_filename=False
        )
        print(f"✅ Uploaded to Cloudinary: {result['secure_url']}")
        return result['secure_url']
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None
