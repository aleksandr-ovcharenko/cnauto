import os
import time
import queue
import threading
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.models import db, Car, CarImage
from backend.utils.file_logger import get_module_logger

logger = get_module_logger(__name__)

# Queue to hold image generation tasks
image_queue = queue.Queue()

# Track task status
task_status: Dict[str, Dict[str, Any]] = {}

# Lock for thread-safe access to task_status
status_lock = threading.Lock()

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
        # Run the generator function with app context
        with app.app_context():
            # Get car to verify it still exists
            car = Car.query.get(task.car_id)
            if not car:
                logger.warning(f"⚠️ Car {task.car_id} not found, abandoning task {task.task_id}")
                update_task_status(task.task_id, 'failed', error='Car not found')
                return
            
            # Run the generator function
            result = task.generator_func(**task.params)
            
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
                # Retry if within retry limit
                if task.retries < task.max_retries:
                    task.retries += 1
                    logger.warning(f"⚠️ Image generation failed, retrying ({task.retries}/{task.max_retries})")
                    update_task_status(task.task_id, 'retrying', error='Generation returned None')
                    time.sleep(task.retry_delay)
                    image_queue.put(task)  # Put back in the queue
                else:
                    logger.error(f"❌ Image generation failed after {task.max_retries} retries")
                    update_task_status(task.task_id, 'failed', error='Max retries exceeded')
    except Exception as e:
        logger.exception(f"❌ Error in image task {task.task_id}: {str(e)}")
        
        # Retry if within retry limit
        if task.retries < task.max_retries:
            task.retries += 1
            logger.warning(f"⚠️ Image generation failed with error, retrying ({task.retries}/{task.max_retries})")
            update_task_status(task.task_id, 'retrying', error=str(e))
            time.sleep(task.retry_delay)
            image_queue.put(task)  # Put back in the queue
        else:
            logger.error(f"❌ Image generation failed after {task.max_retries} retries: {str(e)}")
            update_task_status(task.task_id, 'failed', error=str(e))


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


def start_image_processor(app) -> None:
    """Start the image processor worker thread"""
    worker_thread = threading.Thread(
        target=image_processor_worker,
        args=(app,),
        daemon=True
    )
    worker_thread.start()
    logger.info("✅ Image processor worker thread started")
    
    return worker_thread
