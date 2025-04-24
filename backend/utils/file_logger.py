import os
import logging
import sys
from datetime import datetime

def setup_file_logger():
    """
    Set up a file logger that will reliably write logs to a file
    regardless of the hosting environment.
    
    This function configures both console and file logging for all
    modules in the application.
    """
    # Reset any existing handlers to avoid duplication
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create a logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a timestamped log file
    today = datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(log_dir, f'app_{today}.log')
    
    # Create a formatter that will be used by both handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Set up a file handler for ALL logs (DEBUG and above)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Set up a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    
    # Configure the root logger - this affects all loggers
    root_logger.setLevel(logging.DEBUG)  # Capture everything
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Force debug logs to go to file even if other libraries try to disable it
    logging.getLogger('werkzeug').propagate = True
    logging.getLogger('sqlalchemy').propagate = True
    
    # Reduce verbosity of some loggers in console but keep full logs in file
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    # Add a message to confirm setup
    root_logger.info(f"✅ Logging initialized: All logs will be saved to {log_file}")
    
    return log_file

def get_module_logger(name):
    """
    Get a logger for a module that will log to both console and file.
    
    Usage:
        from backend.utils.file_logger import get_module_logger
        logger = get_module_logger(__name__)
        
        logger.debug("Debug message")
        logger.info("Info message")
    """
    logger = logging.getLogger(name)
    # No need to add handlers, they're inherited from the root logger
    return logger
