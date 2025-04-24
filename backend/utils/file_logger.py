import os
import logging
import sys
import platform
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
    
    # CRITICAL: Force propagation for ALL loggers to ensure logs reach the root logger
    for name in logging.root.manager.loggerDict:
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)  # Set level to DEBUG for all loggers
        logger.propagate = True  # Ensure propagation is enabled

    # Force debug logs to go to file even if other libraries try to disable it
    logging.getLogger('werkzeug').propagate = True
    logging.getLogger('werkzeug').setLevel(logging.DEBUG)
    
    logging.getLogger('sqlalchemy').propagate = True
    logging.getLogger('sqlalchemy').setLevel(logging.DEBUG)
    
    logging.getLogger('flask').propagate = True
    logging.getLogger('flask').setLevel(logging.DEBUG)
    
    # Log some system information to help with debugging
    platform_info = {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'python': platform.python_version(),
        'path': sys.path,
        'cwd': os.getcwd(),
        'env': {k: v for k, v in os.environ.items() if not k.startswith('_')}
    }
    root_logger.info(f"✅ Logging initialized: All logs will be saved to {log_file}")
    root_logger.debug(f"🔧 Platform info: {platform_info}")
    
    # Test logging for each configured logger to verify propagation
    for name in ['werkzeug', 'sqlalchemy', 'flask']:
        if name in logging.root.manager.loggerDict:
            test_logger = logging.getLogger(name)
            test_logger.debug(f"🧪 Test log from {name} logger - propagation={test_logger.propagate}, level={logging.getLevelName(test_logger.level)}")
    
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
    # Ensure this logger has propagation enabled
    logger.propagate = True
    # No need to add handlers, they're inherited from the root logger
    return logger

def add_test_logs():
    """
    Add test log messages at various levels to verify logging is working.
    Call this function from different parts of the application to test logging.
    """
    logger = get_module_logger("test_logger")
    logger.debug("📝 DEBUG test message - should appear in logs")
    logger.info("📝 INFO test message - should appear in logs")
    logger.warning("📝 WARNING test message - should appear in logs")
    logger.error("📝 ERROR test message - should appear in logs")
    logger.critical("📝 CRITICAL test message - should appear in logs")
