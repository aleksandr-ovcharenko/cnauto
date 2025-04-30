import os
import sys

# Add parent directory to path for consistent imports
# This ensures the module can be run directly or imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import event

# Use try-except for imports to support both module and direct script execution
try:
    from backend.models import Car, CarImage
except ImportError:
    from models import Car, CarImage

try:
    from backend.utils.cloudinary_upload import delete_image
except ImportError:
    from utils.cloudinary_upload import delete_image

try:
    from backend.utils.file_logger import get_module_logger
except ImportError:
    from utils.file_logger import get_module_logger

# Use the centralized logger
logger = get_module_logger(__name__)


def setup_deletion_events():
    """
    Set up SQLAlchemy event listeners for deleting Cloudinary resources
    when models are deleted from the database.
    """

    # When a car image is deleted, remove the image from Cloudinary
    @event.listens_for(CarImage, 'after_delete')
    def delete_car_image(mapper, connection, target):
        logger.info(f"CarImage deleted, removing from Cloudinary: ID={target.id}, URL={target.url}")
        if target.url:
            delete_image(url=target.url)

    # When a car is deleted, remove all its images from Cloudinary
    @event.listens_for(Car, 'after_delete')
    def delete_car_with_images(mapper, connection, target):
        logger.info(f"Car deleted, removing all images from Cloudinary: ID={target.id}, Model={target.model}")

        # Delete main image if exists
        if target.image_url:
            delete_image(url=target.image_url)

        # Delete brand logo if exists (only if it's a Cloudinary URL)
        if target.brand_logo and 'cloudinary' in target.brand_logo:
            delete_image(url=target.brand_logo)

        # Delete all gallery images
        # Note: SQLAlchemy should have already deleted the CarImage records due to cascade
        # But let's clean up Cloudinary directly to be sure
        if target.gallery_images:
            for image in target.gallery_images:
                if image.url:
                    delete_image(url=image.url)

        # Delete the entire car folder to catch any missed images
        delete_image(car_id=target.id, car_name=target.model)

    logger.info(" Cloudinary deletion event listeners configured")
