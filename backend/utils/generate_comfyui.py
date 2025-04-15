import json
import os
import tempfile
import traceback

import replicate
import requests
from PIL import Image

REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
DEFAULT_REPLICATE_MODEL = os.getenv("DEFAULT_REPLICATE_MODEL",
                            "fofr/any-comfyui-workflow:8d7883b5a9e7968b4c85dd59c8b4e87351f4a04ac390a426b3b0421e05596e4c")

RAW_WORKFLOW_JSON = """{
  "3": {
    "inputs": {
      "seed": 156680208700286,
      "steps": 10,
      "cfg": 2.5,
      "sampler_name": "dpmpp_2m_sde",
      "scheduler": "karras",
      "denoise": 1,
      "model": ["4", 0],
      "positive": ["6", 0],
      "negative": ["7", 0],
      "latent_image": ["5", 0]
    },
    "class_type": "KSampler",
    "_meta": { "title": "KSampler" }
  },
  "4": {
    "inputs": { "ckpt_name": "SDXL-Flash.safetensors" },
    "class_type": "CheckpointLoaderSimple",
    "_meta": { "title": "Load Checkpoint" }
  },
  "5": {
    "inputs": { "width": 768, "height": 1152, "batch_size": 1 },
    "class_type": "EmptyLatentImage",
    "_meta": { "title": "Empty Latent Image" }
  },
  "6": {
    "inputs": { "text": "placeholder", "clip": ["4", 1] },
    "class_type": "CLIPTextEncode",
    "_meta": { "title": "CLIP Text Encode (Prompt)" }
  },
  "7": {
    "inputs": { "text": "text, watermark", "clip": ["4", 1] },
    "class_type": "CLIPTextEncode",
    "_meta": { "title": "CLIP Text Encode (Prompt)" }
  },
  "8": {
    "inputs": { "samples": ["3", 0], "vae": ["4", 2] },
    "class_type": "VAEDecode",
    "_meta": { "title": "VAE Decode" }
  },
  "9": {
    "inputs": { "filename_prefix": "ComfyUI", "images": ["8", 0] },
    "class_type": "SaveImage",
    "_meta": { "title": "Save Image" }
  }
}""".strip()


def convert_to_webp(input_path, output_path):
    image = Image.open(input_path).convert("RGB")
    image.save(output_path, "webp", quality=90)


def generate_with_comfyui(image_url: str, prompt: str, car_model, car_brand, car_id=None) -> str:
    try:
        # Скачиваем изображение по image_url
        response = requests.get(image_url)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_image:
            temp_image.write(response.content)
            input_image_path = temp_image.name

        print("⚙️ Используем prompt:", prompt)
        workflow = json.loads(RAW_WORKFLOW_JSON)
        workflow["6"]["inputs"]["text"] = prompt

        input_params = {
            "prompt": prompt,
            "output_format": "png",
            "input_image": open(input_image_path, "rb"),
            "workflow_json": json.dumps(workflow),
            "output_quality": 80,
            "randomise_seeds": True,
            "force_reset_cache": False,
            "return_temp_files": False
        }

        print("⚙️ Отправка на Replicate...")
        print(f"Replicate= {DEFAULT_REPLICATE_MODEL}")
        output = replicate.run(DEFAULT_REPLICATE_MODEL, input=input_params)
        print("✅ Ответ от Replicate получен")

    except Exception as e:
        print("⚠️ Ошибка при генерации изображения!")
        traceback.print_exc()
        return None

    if not output:
        print("⚠️ Пустой результат от Replicate")
        return None

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_png:
        output_path = temp_png.name
        temp_png.write(output.read())

    webp_path = output_path.replace(".png", ".webp")
    convert_to_webp(output_path, webp_path)

    try:
        from utils.cloudinary_upload import upload_image
        uploaded_url = upload_image(
            webp_path,
            car_id=car_id,
            car_name=car_model,
            is_main=True
        )
        if uploaded_url:
            print(f"📤 Загрузили .webp изображение: {uploaded_url}")
            os.remove(output_path)
            os.remove(webp_path)
        return uploaded_url
    except Exception as e:
        print("❌ Ошибка при загрузке изображения:", e)
        return None
