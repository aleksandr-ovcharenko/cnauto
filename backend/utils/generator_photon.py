import os
import sys
import tempfile
import json

import requests

# Reset the path helper for relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import replicate
from PIL import Image

from utils.file_logger import get_module_logger
from utils.cloudinary_upload import upload_image

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


def generate_with_photon(prompt: str, image_url: str, car_model: str, car_brand: str, car_id=None) -> str:
    """
    Generate an image using the Replicate Photon API
    
    Args:
        prompt: Text prompt for image generation
        image_url: URL of the reference image 
        car_model: Car model name
        car_brand: Brand name (as string, not a Brand object)
        car_id: Optional car ID for reference
        
    Returns:
        URL of the generated image uploaded to Cloudinary, or None if failed
    """
    try:
        # Check if the API token is set
        if not os.getenv("REPLICATE_API_TOKEN"):
            logger.error("❌ REPLICATE_API_TOKEN environment variable is not set")
            return None

        # Validate image URL before sending to Replicate
        try:
            if not image_url or not image_url.startswith(('http://', 'https://')):
                logger.error(f"❌ Invalid image URL format: {image_url}")
                return None
                
            # Check if image is accessible
            head_response = requests.head(image_url, timeout=5)
            if head_response.status_code != 200:
                logger.error(f"❌ Cannot access image URL (status {head_response.status_code}): {image_url}")
                return None
                
            # Check content type
            content_type = head_response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"⚠️ URL may not be an image (Content-Type: {content_type}): {image_url}")
                # Continue anyway as some URLs may be mislabeled
        except Exception as e:
            logger.warning(f"⚠️ Failed to validate image URL: {str(e)}")
            # Continue anyway as image might still be valid

        logger.info("⚙️ Generating with Luma Photon...")
        input_params = {
            "prompt": prompt,
            "aspect_ratio": REPLICATE_PHOTON_DEFAULTS["aspect_ratio"],
            "image_reference_url": image_url,
            "image_reference_weight": REPLICATE_PHOTON_DEFAULTS["image_reference_weight"],
            "style_reference_weight": REPLICATE_PHOTON_DEFAULTS["style_reference_weight"]
        }

        logger.info(f"📡 Sending request to Replicate...")
        logger.debug(f"📝 Input parameters: {json.dumps(input_params, indent=2)}")
        
        try:
            output = replicate.run(REPLICATE_PHOTON_MODEL, input=input_params)
            
            if not output:
                logger.error("❌ No output received from Replicate")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error calling Replicate API: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON response from Replicate: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Error generating image with Photon: {str(e)}")
            logger.exception("Traceback:")
            return None

        output_url = output[0] if isinstance(output, list) and output else output
        if not output_url or not isinstance(output_url, str):
            logger.error(f"❌ Invalid output from Replicate: {output}")
            return None
            
        logger.info(f"📥 Downloading generated image from: {output_url}")

    except Exception as e:
        logger.error(f"❌ Error processing Photon generated image: {str(e)}")
        logger.exception("Traceback:")
        return None

    try:
        # Download the generated image
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
                    car_name=car_model,
                    car_brand=car_brand,
                    is_main=True,
                    index="ai"
                )
                logger.info(f"☁️ Uploaded AI-generated image to Cloudinary: {cloudinary_url}")
                return cloudinary_url

    except Exception as e:
        logger.error(f"❌ Error processing Photon generated image: {str(e)}")
        logger.exception("Traceback:")
        return None
