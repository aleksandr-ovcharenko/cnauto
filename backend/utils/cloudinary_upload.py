import cloudinary
import cloudinary.api
import cloudinary.uploader
from flask import current_app

from utils.file_logger import get_module_logger

# Use the centralized logger
logger = get_module_logger(__name__)


def upload_image(file, car_id=None, car_name=None, car_brand=None, is_main=False, index=None):
    try:
        # Get base folder from app config or use default
        try:
            base_folder = current_app.config.get("CLOUDINARY_FOLDER", "cn-auto/misc")
        except RuntimeError:
            # Fallback if no application context is available
            logger.warning("⚠️ No Flask application context - using default Cloudinary folder")
            base_folder = "cn-auto/misc"

        base_name = f"{car_name or 'car'}-{'main' if is_main else f'gallery_{index}'}".lower().replace(" ", "-")
        # Путь: <окружение>/cars/<id>-<brand>-<model>/
        folder_name = car_name or 'unknown'
        if car_brand:
            folder_name = f"{car_brand}-{folder_name}"
        car_folder = f"{base_folder}/cars/{car_id or 'unknown'}-{folder_name}".replace(" ", "-")
        logger.info(f"📂 Загрузка в Cloudinary → Папка: {car_folder} | Файл: {base_name}")

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
            logger.info(f"✅ Uploaded to Cloudinary: {result['secure_url']}")
            return result['secure_url']
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return None
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return None


def delete_image(url=None, public_id=None, folder=None, car_id=None, car_name=None, car_brand=None):
    """
    Delete an image from Cloudinary
    
    Can be called with either:
    - url: The full Cloudinary URL
    - public_id: The public ID of the image
    - folder and car_id + car_name: To delete an entire folder
    
    Returns True if successful, False otherwise
    """
    try:
        if url:
            # Skip if URL is not a Cloudinary URL
            if not url or 'cloudinary' not in url:
                logger.debug(f"Skipping non-Cloudinary URL: {url}")
                return True  # Consider it a success if not a Cloudinary URL

            # Extract public_id from URL
            # URL format: https://res.cloudinary.com/cloud_name/image/upload/v1234567890/folder/public_id.ext
            parts = url.split('/')
            if 'upload' in parts:
                upload_index = parts.index('upload')
                # Extract everything after the version (v1234567890)
                # Skip the version part (starts with 'v')
                version_index = upload_index + 1
                if version_index < len(parts) and parts[version_index].startswith('v'):
                    public_id = '/'.join(parts[version_index + 1:])
                    # Remove extension
                    if '.' in public_id:
                        public_id = public_id.rsplit('.', 1)[0]
                    logger.debug(f"Extracted public_id from URL: {public_id}")

        if public_id:
            logger.info(f"Deleting Cloudinary image with public_id: {public_id}")
            try:
                result = cloudinary.uploader.destroy(public_id)
                success = result.get('result') == 'ok'
                if success:
                    logger.info(f"✅ Deleted image from Cloudinary: {public_id}")
                else:
                    # Check for "not found" response
                    if 'not found' in str(result).lower():
                        logger.info(f"⚠️ Image not found in Cloudinary, already deleted: {public_id}")
                        return True  # Consider it a success if already deleted
                    logger.warning(f"❌ Failed to delete image: {result}")
                return success
            except cloudinary.exceptions.NotFound:
                # Image was not found, consider this a success
                logger.info(f"⚠️ Image not found in Cloudinary, already deleted: {public_id}")
                return True

        elif folder:
            # Delete all images in a folder
            logger.info(f"Deleting all images in Cloudinary folder: {folder}")
            try:
                # Check if the folder exists first by listing resources
                resources = cloudinary.api.resources(prefix=folder, max_results=1, resource_type="image")
                if not resources.get('resources'):
                    logger.info(f"⚠️ No resources found in folder {folder}, may be already deleted")
                else:
                    result = cloudinary.api.delete_resources_by_prefix(folder, resource_type="image")

                # Try to delete the folder itself, but handle if it doesn't exist
                try:
                    cloudinary.api.delete_folder(folder, resource_type="image")
                    logger.info(f"✅ Deleted folder from Cloudinary: {folder}")
                except Exception as folder_err:
                    logger.info(f"⚠️ Could not delete folder {folder}: {str(folder_err)}")

                return True
            except Exception as folder_error:
                logger.warning(f"⚠️ Error managing folder {folder}: {str(folder_error)}")
                # Still return True since this is not a critical failure
                return True

        elif car_id and car_name:
            # Construct folder path and delete it
            try:
                base_folder = current_app.config.get("CLOUDINARY_FOLDER", "cn-auto/misc")
            except RuntimeError:
                # Fallback if no application context is available
                logger.warning("⚠️ No Flask application context - using default Cloudinary folder")
                base_folder = "cn-auto/misc"

            folder_name = car_name or 'unknown'
            if car_brand:
                folder_name = f"{car_brand}-{folder_name}"
            car_folder = f"{base_folder}/cars/{car_id or 'unknown'}-{folder_name}"
            logger.info(f"Deleting car folder from Cloudinary: {car_folder}")

            try:
                # Check if the folder exists first by listing resources
                resources = cloudinary.api.resources(prefix=car_folder, max_results=1, resource_type="image")
                if not resources.get('resources'):
                    logger.info(f"⚠️ No resources found in car folder {car_folder}, may be already deleted")
                else:
                    # Delete all resources in the folder with resource_type specified
                    result = cloudinary.api.delete_resources_by_prefix(car_folder, resource_type="image")

                # Try to delete the folder itself
                try:
                    # Specify resource_type to fix the 400 error
                    cloudinary.api.delete_folder(car_folder, resource_type="image")
                    logger.info(f"✅ Deleted car folder from Cloudinary: {car_folder}")
                except Exception as folder_error:
                    logger.warning(f"⚠️ Could not delete car folder structure: {str(folder_error)}")

                return True
            except Exception as folder_error:
                logger.warning(f"⚠️ Error managing car folder {car_folder}: {str(folder_error)}")
                # Still return True since this is not a critical failure
                return True

        else:
            logger.error("❌ No URL, public_id, or folder provided for deletion")
            return False

    except Exception as e:
        logger.error(f"❌ Error deleting from Cloudinary: {str(e)}")
        return False
