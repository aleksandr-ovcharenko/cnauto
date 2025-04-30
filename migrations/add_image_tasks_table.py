"""
Add image_tasks table migration script

This script checks if the image_tasks table exists and creates it if it doesn't.
"""
import os
import sys
import logging

# Add parent directory to path for imports to work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.db import db
    from backend.models import ImageTask
except ImportError:
    from db import db
    from models import ImageTask

try:
    from backend.utils.file_logger import get_module_logger
except ImportError:
    from utils.file_logger import get_module_logger

logger = get_module_logger(__name__)

def run_migration():
    """Check if the image_tasks table exists and create it if not"""
    from sqlalchemy import inspect, text
    
    logger.info("Starting migration: Checking for image_tasks table...")
    inspector = inspect(db.engine)
    table_exists = 'image_tasks' in inspector.get_table_names()
    
    if not table_exists:
        logger.info("image_tasks table does not exist, creating it...")
        try:
            # Create the table using the model metadata
            ImageTask.__table__.create(db.engine)
            logger.info("✅ Successfully created image_tasks table")
        except Exception as e:
            logger.error(f"❌ Error creating image_tasks table: {e}")
            raise
    else:
        logger.info("✅ image_tasks table already exists")
    
    logger.info("Migration completed successfully")
    return True

if __name__ == "__main__":
    logger.info("🚀 Running image_tasks table migration...")
    with db.app.app_context():
        run_migration()
