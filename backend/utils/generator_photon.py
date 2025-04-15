import os
import tempfile
import traceback

import replicate
import requests
from PIL import Image

from utils.cloudinary_upload import upload_image

REPLICATE_PHOTON_MODEL = os.getenv("REPLICATE_PHOTON_MODEL", "luma/photon")
REPLICATE_PHOTON_DEFAULTS = {
    "aspect_ratio": "3:4",
    "image_reference_weight": 1,
    "style_reference_weight": 0.85
}


def convert_to_webp(input_path, output_path):
    image = Image.open(input_path).convert("RGB")
    image.save(output_path, "webp", quality=90)


def generate_with_photon(prompt: str, image_url: str, car_model: str, car_brand, car_id=None) -> str:
    try:
        print("⚙️ Генерация через Luma Photon...")
        input_params = {
            "prompt": prompt,
            "aspect_ratio": REPLICATE_PHOTON_DEFAULTS["aspect_ratio"],
            "image_reference_url": image_url,
            "image_reference_weight": REPLICATE_PHOTON_DEFAULTS["image_reference_weight"],
            "style_reference_weight": REPLICATE_PHOTON_DEFAULTS["style_reference_weight"]
        }

        print("📡 Отправка запроса в Replicate...")
        output = replicate.run(REPLICATE_PHOTON_MODEL, input=input_params)
        print("✅ Изображение получено")

    except Exception as e:
        print("❌ Ошибка при генерации через Photon:")
        traceback.print_exc()
        return None

    if not output:
        print("⚠️ Нет результата от Photon")
        return None

    # Скачиваем результат
    try:
        response = requests.get(output)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(response.content)
            png_path = tmp.name
    except Exception as e:
        print("❌ Ошибка при загрузке результата:", e)
        return None

    webp_path = png_path.replace(".png", ".webp")
    convert_to_webp(png_path, webp_path)

    try:
        uploaded_url = upload_image(
            webp_path,
            car_id=car_id,
            car_name=car_model,
            is_main=True
        )
        if uploaded_url:
            print(f"📤 Загружено в Cloudinary: {uploaded_url}")
            os.remove(png_path)
            os.remove(webp_path)
        return uploaded_url
    except Exception as e:
        print("❌ Ошибка при загрузке в Cloudinary:", e)
        return None
