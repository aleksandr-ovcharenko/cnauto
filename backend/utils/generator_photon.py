import os
import tempfile
import traceback

import replicate
import requests
from PIL import Image

from backend.utils.cloudinary_upload import upload_image
from backend.utils.file_logger import get_module_logger

# Use the centralized logger
logger = get_module_logger(__name__)

REPLICATE_PHOTON_MODEL = os.getenv("REPLICATE_PHOTON_MODEL", "luma/photon")
REPLICATE_PHOTON_DEFAULTS = {
    "aspect_ratio": "3:4",
    "image_reference_weight": 1,
    "style_reference_weight": 0.85
}


def convert_to_webp(input_path, output_path):
    image = Image.open(input_path).convert("RGB")
    image.save(output_path, "webp", quality=90)


def check_replicate_api_token():
    """Check if the Replicate API token is set and valid"""
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        logger.error("❌ REPLICATE_API_TOKEN environment variable is not set")
        return False
    
    # Validate the token by making a test request
    try:
        # Use the client directly to make a request to the API
        replicate.Client(api_token=token).models.get("luma/photon")
        logger.info("✅ REPLICATE_API_TOKEN is valid")
        return True
    except Exception as e:
        logger.error(f"❌ REPLICATE_API_TOKEN is invalid or API is unavailable: {str(e)}")
        return False


def generate_with_photon(prompt: str, image_url: str, car_model: str, car_brand, car_id=None) -> str:
    try:
        # Check if the API token is set
        if not os.getenv("REPLICATE_API_TOKEN"):
            logger.error("❌ REPLICATE_API_TOKEN environment variable is not set")
            return None
            
        logger.info("⚙️ Generating with Luma Photon...")
        input_params = {
            "prompt": prompt,
            "aspect_ratio": REPLICATE_PHOTON_DEFAULTS["aspect_ratio"],
            "image_reference_url": image_url,
            "image_reference_weight": REPLICATE_PHOTON_DEFAULTS["image_reference_weight"],
            "style_reference_weight": REPLICATE_PHOTON_DEFAULTS["style_reference_weight"]
        }

        logger.info("📡 Sending request to Replicate...")
        output = replicate.run(REPLICATE_PHOTON_MODEL, input=input_params)
        logger.info("✅ Image received from Replicate")

    except Exception as e:
        logger.error(f"❌ Error generating image with Photon: {str(e)}")
        logger.exception("Traceback:")
        return None

    try:
        # Download the generated image
        if not output:
            logger.error("❌ No output received from Replicate")
            return None

        output_url = output[0] if isinstance(output, list) and output else output
        logger.info(f"📥 Downloading generated image from: {output_url}")

        # Upload to Cloudinary
        with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_jpg:
            with tempfile.NamedTemporaryFile(suffix=".webp") as temp_webp:
                # Download the image
                response = requests.get(output_url)
                temp_jpg.write(response.content)
                temp_jpg.flush()

                # Convert to WebP for better compression
                convert_to_webp(temp_jpg.name, temp_webp.name)

                # Upload to Cloudinary
                cloudinary_url = upload_image(
                    temp_webp.name,
                    car_id=car_id,
                    car_name=f"{car_brand} {car_model} AI",
                    is_main=False,
                    index="ai"
                )
                logger.info(f"☁️ Uploaded AI-generated image to Cloudinary: {cloudinary_url}")
                return cloudinary_url

    except Exception as e:
        logger.error(f"❌ Error processing Photon generated image: {str(e)}")
        logger.exception("Traceback:")
        return None
