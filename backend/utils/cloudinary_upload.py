from cloudinary_config import cloudinary
import cloudinary.uploader

def upload_image(file):
    print("📤 Загружаем файл в Cloudinary:", file.filename)
    try:
        result = cloudinary.uploader.upload(file)
        print("✅ Успешная загрузка:", result['secure_url'])
        return result['secure_url']
    except Exception as e:
        print("❌ Ошибка при загрузке в Cloudinary:", e)
        return None
