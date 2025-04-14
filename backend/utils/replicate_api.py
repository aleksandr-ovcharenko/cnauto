import os
import traceback

import replicate
from cloudinary.uploader import upload_image

REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")


def generate_main_image(image_url: str, car_model, car_brand) -> str:
    """
     Отправляет изображение на Replicate (image-to-image),
     получает результат и сохраняет его в Cloudinary.

     :param image_url: URL исходного изображения
     :param car_model: Название модели, используется в prompt
     :param car_brand: Бренд модели, используется в prompt
     :return: Ссылка на загруженное изображение или None
     """

    prompt = (
        f"Очисти это фото, чтобы эта модель стояла одна, "
        f"на номере напиши cnauto.ru. "
        f"Поверни ее мордой влево и вперед и зад направь вправо и назад, по диоганали. "
        f"Модель: {car_brand.name} {car_model}"
    )

    try:
        print("⚙️ Отправка на Replicate...")
        print("📷 Изображение:", image_url)
        print("🧠 Prompt:", prompt)

        output = replicate.run(
            "stability-ai/stable-diffusion-inpainting",
            input={
                "image": image_url,
                "prompt": prompt,
                "prompt_strength": 0.85,
                "guidance_scale": 8,
                "num_inference_steps": 50,
                "width": 800,
                "height": 600
            }
        )
        print("✅ Ответ от Replicate получен")
    except Exception as e:
        print("⚠️ Ошибка при генерации изображения!")
        print("💥 Тип ошибки:", type(e).__name__)
        print("📄 Подробности:")
        traceback.print_exc()
        return None

    result_url = output[-1] if isinstance(output, list) else output
    if not result_url:
        print("⚠️ Не удалось получить ссылку на результат")
        return None

    uploaded_url = upload_image(result_url, car_id=None, car_name=car_model, is_main=True)
    if uploaded_url:
        print(f"📤 Загрузили главное изображение: {uploaded_url}")
    return uploaded_url
