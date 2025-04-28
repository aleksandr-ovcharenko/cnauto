#!/usr/bin/env python3
"""
Quick script to check brand trims in the database
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Import models directly
from backend.models import Brand, BrandTrim

# Create a direct database connection using SQLAlchemy
def get_db_session():
    """Get a SQLAlchemy session directly without Flask-SQLAlchemy"""
    # Get database URI from environment or use default
    database_url = os.environ.get('DATABASE_URL', 'postgresql://cnauto:cnauto@localhost:5432/cnauto_db')
    
    # Handle SQLAlchemy 1.4+ compatibility for postgres URLs
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Create engine and session
    engine = create_engine(database_url)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    return Session()

def check_trim_counts():
    """Check how many trims are in the database for each brand"""
    session = get_db_session()
    try:
        # Get all brands with trim counts
        brands = session.query(Brand).all()
        
        print("BRAND TRIMS REPORT")
        print("=" * 50)
        total_trims = 0
        
        for brand in brands:
            trim_count = session.query(BrandTrim).filter(BrandTrim.brand_id == brand.id).count()
            if trim_count > 0:
                total_trims += trim_count
                print(f"{brand.name}: {trim_count} trims")
        
        print("=" * 50)
        print(f"Total trims in database: {total_trims}")
    finally:
        session.close()

if __name__ == "__main__":
    check_trim_counts()
