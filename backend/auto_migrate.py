"""
Helper module to suggest running migrations during app startup
"""
import os
import logging

logger = logging.getLogger(__name__)

def run_migrations(app, db, migrations_dir):
    """Check migration status and log appropriate message"""
    try:
        from alembic.migration import MigrationContext
        from alembic.script import ScriptDirectory
        from alembic.config import Config
        
        # Get current database version directly from the database
        with app.app_context():
            # Get a connection from the engine directly
            connection = db.engine.connect()
            
            # Get current version from database
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            
            # Get the migrations directory and determine its latest version
            alembic_ini_path = os.path.join(os.path.dirname(migrations_dir), 'alembic.ini')
            alembic_cfg = Config(alembic_ini_path)
            script = ScriptDirectory.from_config(alembic_cfg)
            head_revs = script.get_revisions(script.get_heads())
            
            if not current_rev:
                logger.warning("⚠️ Database may not be migrated. Run 'flask db upgrade' to apply migrations.")
            elif current_rev != script.get_heads()[0]:
                logger.warning(f"⚠️ Database is at version {current_rev} but latest is {script.get_heads()[0]}.")
                logger.warning("⚠️ Run 'cd backend && PYTHONPATH=.. python -m flask db upgrade' to update.")
            else:
                logger.info("✅ Database schema is up to date")
                
            connection.close()
            
    except Exception as e:
        logger.warning(f"⚠️ Could not verify migration status: {str(e)}")
        logger.warning("⚠️ Make sure to run 'cd backend && PYTHONPATH=.. python -m flask db upgrade' if needed")
