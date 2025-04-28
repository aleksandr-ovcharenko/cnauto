#!/usr/bin/env python3
"""
Seed script to populate the BrandTrim table with common trim levels for different car brands.
This ensures the system can recognize typical trims during car data parsing.

Usage:
    cd backend
    python seeds/brand_trims.py
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Add the parent directory to the path so we can import our models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import models directly
from models import Brand, BrandTrim

# Configure logging
from utils.file_logger import get_module_logger
logger = get_module_logger(__name__)

# Create a direct database connection using SQLAlchemy
def get_db_session():
    """Get a SQLAlchemy session directly without Flask-SQLAlchemy"""
    database_url = os.environ.get('DATABASE_URL', 'postgresql://cnauto:cnauto@localhost:5432/cnauto_db')
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    engine = create_engine(database_url)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    return Session()

# Main trims dictionary
BRAND_TRIMS = {
    # German Brands
    "BMW": [
        "Base", "Sport", "M Sport", "Luxury", "xLine", "M Performance", "Competition", 
        "Individual", "Executive", "Pure Excellence", "M Sport Pro", "M Sport X", "First Edition"
    ],
    "Mercedes-Benz": ["Base", "AMG", "AMG Line", "Avantgarde", "Exclusive", "Premium", "Night Edition", "Edition 1"],
    "Audi": [
        "Base", "Premium", "Premium Plus", "Prestige", "S Line", "Black Edition", "Sport", 
        "RS", "Competition", "Design", "Technology", "Advanced", "Ultra"
    ],
    "Volkswagen": ["Base", "S", "SE", "SEL", "R-Line", "R", "GTI", "GTE", "GLI", "Life", "Style", "Executive"],
    "Porsche": ["Base", "S", "4S", "Turbo", "Turbo S", "GTS", "GT3", "Targa", "Exclusive", "RS"],

    # Japanese Brands
    "Toyota": [
        "L", "LE", "SE", "XLE", "XSE", "Limited", "Platinum", "TRD", "Adventure", "Hybrid", "Prestige Safety"
    ],
    "Honda": ["LX", "EX", "Sport", "Touring", "Elite", "Type R", "Black Edition", "Hybrid"],
    "Lexus": ["Base", "Premium", "Luxury", "F SPORT", "Ultra Luxury", "Executive", "Black Line"],
    "Nissan": ["S", "SV", "SL", "SR", "Platinum", "NISMO", "Midnight Edition", "Rock Creek"],

    # Korean Brands
    "Hyundai": ["SE", "SEL", "Limited", "Ultimate", "N Line", "Sport", "Calligraphy", "Preferred"],
    "Kia": ["LX", "EX", "GT-Line", "SX", "GT", "Sport", "Prestige", "Hybrid"],

    # American Brands
    "Ford": ["S", "SE", "SEL", "Titanium", "Limited", "ST", "Raptor", "Platinum"],
    "Chevrolet": ["LS", "LT", "Premier", "High Country", "RS", "ZR2", "SS", "Trail Boss"],
    "Jeep": ["Sport", "Latitude", "Limited", "Trailhawk", "Summit", "Overland", "Rubicon"],
    "Tesla": ["Standard Range", "Long Range", "Performance", "Plaid", "Dual Motor"],

    # European Others
    "Volvo": ["Momentum", "Inscription", "R-Design", "Cross Country", "Ultimate"],
    "Land Rover": ["Base", "S", "SE", "HSE", "Autobiography", "First Edition", "Dynamic"],
    "Jaguar": ["Base", "Prestige", "R-Sport", "SVR", "Checkered Flag", "First Edition"],

    # Chinese Brands
    "Chery": ["Comfort", "Luxury", "Premium", "Elite", "Flagship", "Royal", "Supreme"],
    "Geely": ["Comfort", "Luxury", "Premium", "Flagship", "Elite", "Sport"],
    "Haval": ["Comfort", "Luxury", "Premium", "Ultra", "Top", "Red Label", "Blue Label"],
    "Exeed": ["Comfort", "Luxury", "Premium", "Flagship", "Supreme", "Executive"],
    "Changan": ["Comfort", "Luxury", "Premium", "Elite", "Supreme", "Flagship"],
    "BYD": ["Comfort", "Luxury", "Premium", "Flagship", "Champion", "Plus", "Pro", "Ultimate"],
    "Omoda": ["Comfort", "Luxury", "Premium", "Flagship", "Supreme", "S5", "C5"],
    "Jaecoo": ["Comfort", "Luxury", "Premium", "Ultimate", "Elite", "Flagship"],
    "Voyah": ["Free", "Dream", "Long Range", "Executive", "Supreme", "EREV"],
    "Hongqi": ["Standard", "Deluxe", "Flagship", "Executive", "Royal", "Presidential"],
    "FAW": ["Comfort", "Luxury", "Premium", "Flagship", "Elite", "Bestune"],
    "NIO": ["Base", "Signature Edition", "Performance", "Premier Edition", "Standard", "Long Range"],
    "Jeep": ["Sport", "Latitude", "Limited", "Trailhawk", "Rubicon", "Overland", "Summit", "Altitude"],
    "JAC": ["Standard", "Comfort", "Luxury", "Elite", "Premium", "Flagship"],
}

def seed_brand_trims(session):
    """Seed the BrandTrim table with common trims."""
    logger.info("Starting brand trims seeding process...")

    existing_trims_count = session.query(BrandTrim).count()
    logger.info(f"Found {existing_trims_count} existing brand trims")

    trims_added = 0
    brands_skipped = []

    for brand_name, trims in BRAND_TRIMS.items():
        brand = session.query(Brand).filter(Brand.name == brand_name).first()
        if not brand:
            brands_skipped.append(brand_name)
            continue

        for trim_name in trims:
            existing_trim = session.query(BrandTrim).filter(
                BrandTrim.brand_id == brand.id,
                BrandTrim.name == trim_name
            ).first()
            if existing_trim:
                continue

            new_trim = BrandTrim(
                name=trim_name,
                brand_id=brand.id,
                source='seed_script',
                created_at=datetime.utcnow()
            )
            session.add(new_trim)
            trims_added += 1

            if trims_added % 50 == 0:
                session.commit()
                logger.info(f"Added {trims_added} trims so far...")

    session.commit()

    if brands_skipped:
        logger.warning(f"Skipped {len(brands_skipped)} brands not found in database: {', '.join(brands_skipped)}")

    logger.info(f"✅ Successfully added {trims_added} brand trims")
    return trims_added, brands_skipped

if __name__ == "__main__":
    try:
        session = get_db_session()
        trims_added, brands_skipped = seed_brand_trims(session)
        print(f"✅ Successfully added {trims_added} brand trims")

        if brands_skipped:
            print(f"⚠️ Skipped {len(brands_skipped)} brands:")
            for brand in brands_skipped:
                print(f"  - {brand}")

        session.close()
    except Exception as e:
        logger.error(f"❌ Error seeding brand trims: {e}")
        print(f"❌ Error seeding brand trims: {e}")
        sys.exit(1)
