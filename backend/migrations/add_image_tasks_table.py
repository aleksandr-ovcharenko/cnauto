"""
Migration script to add ImageTask table to the database.
Run this script to create the new image_tasks table for tracking image generation history.
"""

import os
import sys
import logging
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, ImageTask
from app import app
from utils.file_logger import get_module_logger

logger = get_module_logger(__name__)

def run_migration():
    """Create the image_tasks table if it doesn't exist"""
    with app.app_context():
        logger.info("Starting migration to add image_tasks table")
        
        # Check if table exists
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'image_tasks' not in tables:
            logger.info("Creating image_tasks table...")
            
            # Create the table
            ImageTask.__table__.create(db.engine)
            logger.info("✅ image_tasks table created successfully")
            
            # Try to add a test record
            try:
                test_task = ImageTask(
                    source='migration_test',
                    status='completed',
                    created_at=datetime.utcnow()
                )
                db.session.add(test_task)
                db.session.commit()
                logger.info(f"✅ Test record added with ID: {test_task.id}")
                
                # Remove the test record
                db.session.delete(test_task)
                db.session.commit()
                logger.info("✅ Test record removed")
            except Exception as e:
                logger.error(f"❌ Error testing table: {e}")
                db.session.rollback()
                
            logger.info("✅ Migration completed successfully")
        else:
            logger.info("image_tasks table already exists, skipping creation")

if __name__ == "__main__":
    run_migration()
