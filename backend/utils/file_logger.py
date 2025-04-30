import logging
import os
import platform
import sys
from datetime import datetime

# Add parent directory to path for consistent imports
# This ensures the module can be run directly or imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


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

    # CRITICAL: Disable existing loggers to prevent them from using their own configuration
    logging.Logger.manager.loggerDict.clear()

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

    # IMPORTANT: Set appropriate log levels for different loggers
    # Need to forcefully set these AFTER clearing the loggerDict

    # Database loggers - reduce verbosity to avoid sensitive data
    # Set ALL SQLAlchemy loggers to ERROR level to silence them completely
    logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)
    logging.getLogger('sqlalchemy.orm').setLevel(logging.ERROR)
    logging.getLogger('sqlalchemy.dialects').setLevel(logging.ERROR)

    # Web server and framework logs - keep at INFO level
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    logging.getLogger('flask').setLevel(logging.INFO)
    logging.getLogger('flask.app').setLevel(logging.INFO)
    logging.getLogger('flask.request').setLevel(logging.INFO)  # Don't log request bodies

    # Our application logs - keep at DEBUG level
    logging.getLogger('utils.file_logger').setLevel(logging.DEBUG)

    # Add a message to confirm setup
    root_logger.info(f"✅ Logging initialized: All logs will be saved to {log_file}")

    # --- PROPAGATION AND HANDLER CHECKS ---
    # Check all loggers for propagate=False or extra handlers
    for name, logger_obj in logging.root.manager.loggerDict.items():
        if isinstance(logger_obj, logging.Logger):
            if hasattr(logger_obj, 'propagate') and not logger_obj.propagate:
                root_logger.warning(
                    f"⚠️ Logger '{name}' has propagate=False: logs may not reach the root logger and file!")
            if hasattr(logger_obj, 'handlers') and logger_obj.handlers:
                root_logger.warning(
                    f"⚠️ Logger '{name}' has its own handlers: {logger_obj.handlers}. This may cause logs to bypass the root logger!")

    # Testing flag to verify logging configuration
    os.environ["LOGGING_INITIALIZED"] = "1"

    # Log some system information to help with debugging
    platform_info = {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'python': platform.python_version(),
        'path': sys.path,
        'cwd': os.getcwd()
    }
    root_logger.debug(f"🔧 Platform info: {platform_info}")

    # Test logging for each configured logger to verify propagation
    for name in ['werkzeug', 'sqlalchemy', 'flask']:
        if name in logging.root.manager.loggerDict:
            test_logger = logging.getLogger(name)
            test_logger.debug(
                f"🧪 Test log from {name} logger - propagation={test_logger.propagate}, level={logging.getLevelName(test_logger.level)}")

    return log_file


def get_module_logger(module_name):
    """
    Get a logger for a module that uses the central configuration.
    Usage in modules:  logger = get_module_logger(__name__)
    """
    return logging.getLogger(module_name)


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
