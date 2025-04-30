# Seed scripts package initialization
import os
import sys

# Add the parent directory to the path so we can import from backend
# This ensures seed scripts can be run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
