"""
Entry point for running the application with `python -m backend`
"""
import os
import logging
from .app import app, logger
from .utils.file_logger import setup_file_logger

# Set up file logging
log_file_path = setup_file_logger()

if __name__ == "__main__":
    with app.app_context():
        logger.info("🔗 login url: %s", app.url_for('admin_login'))
    
    # Get host and port from environment or use defaults
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    
    logger.info(f"🚀 Starting application on http://{host}:{port}")
    app.run(host=host, port=port)
