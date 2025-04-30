import os
import queue
# Use relative imports
import sys
import threading
import time
from datetime import datetime
from typing import Dict, Any, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.models import db, Car, CarImage
from utils.file_logger import get_module_logger

logger = get_module_logger(__name__)

# Queue to hold image generation tasks
image_queue = queue.Queue()

# Track task status
task_status: Dict[str, Dict[str, Any]] = {}

# Lock for thread-safe access to task_status
status_lock = threading.Lock()

# Dictionary to store successfully generated images that had upload failures
# Key: task_id, Value: {"output_url": url, "timestamp": time}
generated_cache = {}
generated_cache_lock = threading.Lock()
CACHE_EXPIRY_SECONDS = 60 * 30  # Cache generated images for 30 minutes

# Clean old entries from the cache periodically
def clean_generated_cache():
    current_time = time.time()
    with generated_cache_lock:
        to_remove = []
        for task_id, data in generated_cache.items():
            if current_time - data["timestamp"] > CACHE_EXPIRY_SECONDS:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del generated_cache[task_id]
            logger.debug(f"Removed expired cache entry for task {task_id}")

def add_to_generated_cache(task_id, output_url):
    """Cache a successfully generated image for later upload attempts"""
    with generated_cache_lock:
        generated_cache[task_id] = {
            "output_url": output_url,
            "timestamp": time.time()
        }
        logger.info(f"✅ Cached generated image URL for task {task_id}")

def get_from_generated_cache(task_id):
    """Retrieve a cached generated image if available"""
    clean_generated_cache()  # Clean expired entries
    with generated_cache_lock:
        if task_id in generated_cache:
            return generated_cache[task_id]["output_url"]
    return None

class ImageTask:
    """Represents an image generation task"""

    def __init__(self,
                 task_id: str,
                 car_id: int,
                 generator_func: callable,
                 params: Dict[str, Any],
                 max_retries: int = 3,
                 retry_delay: int = 30):
        self.task_id = task_id
        self.car_id = car_id
        self.generator_func = generator_func
        self.params = params
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retries = 0
        self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for status tracking"""
        return {
            'task_id': self.task_id,
            'car_id': self.car_id,
            'status': 'pending',
            'retries': self.retries,
            'created_at': self.created_at.isoformat(),
            'last_update': datetime.now().isoformat(),
            'result': None,
            'error': None
        }


def enqueue_image_task(car_id: int, generator_func: callable, params: Dict[str, Any], max_retries: int = 3) -> str:
    """Add an image generation task to the queue"""
    task_id = f"img_task_{car_id}_{int(time.time())}"

    task = ImageTask(
        task_id=task_id,
        car_id=car_id,
        generator_func=generator_func,
        params=params,
        max_retries=max_retries
    )

    # Add to queue
    image_queue.put(task)

    # Record initial status
    with status_lock:
        task_status[task_id] = task.to_dict()

    logger.info(f"✅ Added image task to queue: {task_id} for car_id={car_id}")
    return task_id


def update_task_status(task_id: str, status: str, result: Any = None, error: str = None) -> None:
    """Update the status of a task"""
    with status_lock:
        if task_id in task_status:
            task_status[task_id].update({
                'status': status,
                'last_update': datetime.now().isoformat(),
                'result': result,
                'error': error
            })
            logger.debug(f"Task {task_id} status updated to {status}")


def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get the current status of a task"""
    with status_lock:
        return task_status.get(task_id, {'status': 'unknown', 'error': 'Task not found'})


def get_car_tasks(car_id: int) -> List[Dict[str, Any]]:
    """Get all tasks for a specific car"""
    with status_lock:
        return [task for task in task_status.values() if task.get('car_id') == car_id]


def process_image_task(task: ImageTask, app) -> None:
    """Process a single image generation task"""
    logger.info(f"🔄 Processing image task {task.task_id} for car_id={task.car_id}")

    # Update status to processing
    update_task_status(task.task_id, 'processing')

    try:
        # Check if we already have a generated image for this task (to avoid redundant generation)
        cached_output_url = get_from_generated_cache(task.task_id)
        
        # Run the generator function with app context
        with app.app_context():
            # Get car to verify it still exists
            car = Car.query.get(task.car_id)
            if not car:
                logger.warning(f"⚠️ Car {task.car_id} not found, abandoning task {task.task_id}")
                update_task_status(task.task_id, 'failed', error='Car not found')
                return
                
            # If we have a cached generated image, skip generation and try upload directly
            result = None
            if cached_output_url:
                logger.info(f"💾 Using cached generated image for task {task.task_id}")
                
                # Try to download and upload the cached image
                try:
                    import tempfile
                    import requests
                    from utils.cloudinary_upload import upload_image
                    
                    logger.info(f"⬇️ Downloading cached image from: {cached_output_url}")
                    with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_jpg:
                        with tempfile.NamedTemporaryFile(suffix=".webp") as temp_webp:
                            # Download the image
                            response = requests.get(cached_output_url)
                            temp_jpg.write(response.content)
                            temp_jpg.flush()
                            
                            # Convert to WebP using the same function as in generator_photon
                            try:
                                from utils.generator_photon import convert_to_webp
                                convert_to_webp(temp_jpg.name, temp_webp.name)
                            except ImportError:
                                # Fallback if conversion function not available
                                import shutil
                                shutil.copy(temp_jpg.name, temp_webp.name)
                            
                            # Upload to Cloudinary
                            result = upload_image(
                                temp_webp.name,
                                car_id=task.car_id,
                                car_name=task.params.get('car_model', ''),
                                car_brand=task.params.get('car_brand', ''),
                                is_main=True,
                                index="ai"
                            )
                except Exception as e:
                    logger.error(f"❌ Failed to process cached image: {str(e)}")
                    # We'll fall back to normal generation below if result is None
            
            # If no cached image or cached processing failed, run normal generation
            if not result:
                # Separate generation result from upload result
                generator_output_url = None
                
                try:
                    # Run the generator function which should return the uploaded URL
                    result = task.generator_func(**task.params)
                    
                    # If we got None back but no exception, it might be just a Cloudinary upload failure
                    if not result and 'generator_photon' in str(task.generator_func):
                        # Try to extract the output URL from the logs - this is a hacky fallback
                        # but better than regenerating the same image multiple times
                        import re
                        with open("/home/aleks/dev/cnauto-site/backend/logs/app_20250430.log", "r") as f:
                            log_content = f.read()
                            match = re.search(f"Downloading generated image from: (https?://.*?)\\n", log_content)
                            if match:
                                generator_output_url = match.group(1)
                                logger.info(f"📝 Extracted generated image URL from logs: {generator_output_url}")
                                if generator_output_url:
                                    add_to_generated_cache(task.task_id, generator_output_url)
                except Exception as e:
                    logger.error(f"❌ Generator function error: {str(e)}")
                    
            if result:
                # Update the car with the generated image
                car.image_url = result

                # Also create a gallery image
                gallery_image = CarImage(
                    car_id=task.car_id,
                    url=result,
                    title=f"AI Generated {datetime.now().strftime('%Y-%m-%d')}",
                    alt="AI generated image",
                    position=999  # High position to put it at the end
                )
                db.session.add(gallery_image)
                db.session.commit()

                logger.info(f"✅ Successfully processed image task {task.task_id}, image saved: {result}")
                update_task_status(task.task_id, 'completed', result=result)
            else:
                # If we've cached a generated image, don't retry the generation
                if generator_output_url:
                    logger.warning(f"⚠️ Image upload failed, but generation succeeded. Will retry upload later.")
                    update_task_status(task.task_id, 'waiting_upload', error='Upload failed but generation succeeded')
                    # Put back in queue with lower retry count
                    time.sleep(task.retry_delay)
                    image_queue.put(task)
                # Retry if within retry limit
                elif task.retries < task.max_retries:
                    task.retries += 1
                    logger.warning(f"⚠️ Image generation failed, retrying ({task.retries}/{task.max_retries})")
                    update_task_status(task.task_id, 'retrying', error='Generation returned None')
                    time.sleep(task.retry_delay)
                    image_queue.put(task)  # Put back in the queue
                else:
                    logger.error(f"❌ Image generation failed after {task.max_retries} attempts")
                    update_task_status(task.task_id, 'failed', error=f'Failed after {task.max_retries} attempts')
    except Exception as e:
        logger.error(f"❌ Unexpected error processing task {task.task_id}: {str(e)}")
        logger.exception("Traceback:")
        
        # Retry if within retry limit
        if task.retries < task.max_retries:
            task.retries += 1
            logger.warning(f"⚠️ Processing error, retrying ({task.retries}/{task.max_retries})")
            update_task_status(task.task_id, 'retrying', error=str(e))
            time.sleep(task.retry_delay)
            image_queue.put(task)
        else:
            logger.error(f"❌ Processing failed after {task.max_retries} attempts")
            update_task_status(task.task_id, 'failed', error=f'Error: {str(e)}')


def image_processor_worker(app) -> None:
    """Worker function to process image tasks from the queue"""
    logger.info("🚀 Starting image processor worker")

    while True:
        try:
            # Get a task from the queue
            task = image_queue.get(block=True, timeout=1)

            # Process the task
            process_image_task(task, app)

            # Mark the task as done
            image_queue.task_done()
        except queue.Empty:
            # No tasks in queue, just continue
            pass
        except Exception as e:
            logger.exception(f"❌ Unexpected error in image processor worker: {str(e)}")
            # Sleep a bit to prevent excessive CPU usage in case of recurring errors
            time.sleep(5)

        # Periodically log that the worker is still running
        if int(time.time()) % 120 == 0:  # Log every 2 minutes (approximately)
            logger.debug(f"⚙️ Image processor worker is active - {image_queue.qsize()} tasks in queue")


def start_image_processor(app) -> threading.Thread:
    """Start the image processor worker thread"""
    worker_thread = threading.Thread(
        target=image_processor_worker,
        args=(app,),
        daemon=True
    )
    worker_thread.name = "ImageProcessorThread"  # Name the thread for easier debugging
    worker_thread.start()
    logger.info(f"✅ Image processor worker thread started: {worker_thread.name} (id: {worker_thread.ident})")

    return worker_thread
