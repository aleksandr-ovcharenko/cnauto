"""
Simple script to run migrations on Railways deployment
"""
import os
import sys
import subprocess

def run_alembic_command():
    """Run alembic upgrade directly using subprocess to avoid app context issues"""
    try:
        # Get the path to the alembic.ini file
        alembic_ini = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'alembic.ini'))
        
        # Check if file exists
        if not os.path.exists(alembic_ini):
            print(f"Error: alembic.ini not found at {alembic_ini}")
            return False
            
        # Use subprocess to run alembic directly
        print("Running alembic upgrade head...")
        result = subprocess.run(
            ['alembic', '-c', alembic_ini, 'upgrade', 'head'],
            capture_output=True,
            text=True
        )
        
        # Show output
        print(result.stdout)
        if result.stderr:
            print(f"Error output: {result.stderr}")
            
        # Check result
        if result.returncode != 0:
            print(f"Migration failed with exit code {result.returncode}")
            return False
            
        print("Migration completed successfully!")
        return True
    
    except Exception as e:
        print(f"Error executing migration: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_alembic_command()
    if not success:
        sys.exit(1)
