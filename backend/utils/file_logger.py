import os
import logging
from datetime import datetime

def setup_file_logger():
    """
    Set up a file logger that will reliably write logs to a file
    regardless of the hosting environment.
    """
    # Create a logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a timestamped log file
    today = datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(log_dir, f'app_{today}.log')
    
    # Set up a file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Add the handler to the logger
    logger.addHandler(file_handler)
    
    # Add a message to confirm setup
    logger.info(f"✅ File logging initialized to {log_file}")
    return log_file
