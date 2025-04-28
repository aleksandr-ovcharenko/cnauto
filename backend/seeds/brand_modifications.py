#!/usr/bin/env python3
"""
Seed script to populate the BrandModification table with common modification types for different car brands.
This ensures the system can recognize typical engine configurations, drivetrain types, etc.

Usage:
    cd backend
    python seeds/brand_modifications.py
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

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

# Dictionary of brand modifications by brand name
BRAND_MODIFICATIONS = {
    # German Brands
    "BMW": [
        "1.5", "1.6", "2.0", "3.0", "4.4", "i", "d", "xDrive", "sDrive", "xDrive20", "xDrive30", "xDrive40", 
        "xDrive20d", "xDrive20i", "xDrive30d", "xDrive30i", "xDrive40d", "xDrive40i", "xDrive50i", "M40i", "M50i",
        "sDrive20i", "sDrive30i", "118d", "120i", "220d", "320d", "320i", "330i", "330e", "420d", "520d", "530i", 
        "M", "M Performance", "Competition", "118i", "320i", "330e", "520d", "530i", "X5 xDrive", "M340i", "M550i"
    ],
    "Mercedes-Benz": [
        "180", "200", "220", "250", "300", "320", "350", "400", "450", "500", "580", "600", 
        "E 180", "E 200", "E 220", "E 250", "E 300", "E 320", "E 350", "E 400", "E 450", "E 500", "E 580", "E 600",
        "C 180", "C 200", "C 220", "C 250", "C 300", "C 320", "C 350", "C 400", "C 450", "C 500", "C 580", "C 600",
        "S 350", "S 400", "S 450", "S 500", "S 580", "S 600", "S 650", "S 680",
        "A 180", "A 200", "A 220", "A 250", "A 300", "A 320", "A 350", "A 400",
        "GLA 200", "GLA 250", "GLA 300", "GLA 350", "GLA 45 AMG",
        "GLC 200", "GLC 250", "GLC 300", "GLC 350", "GLC 400", "GLC 43 AMG", "GLC 63 AMG",
        "GLE 300", "GLE 350", "GLE 400", "GLE 450", "GLE 53 AMG", "GLE 63 AMG",
        "AMG", "4MATIC", "BlueEFFICIENCY", "CDI", "CGI", "EQ", "Hybrid", "BlueTEC",
        "2.0T", "3.0T", "3.0 Biturbo", "4.0 Biturbo", "5.5 Biturbo", "6.0 Biturbo",
        "E 300 2.0T", "C 300 2.0T", "S 450 3.0T", "GLC 300 2.0T"
    ],
    "Audi": [
        "1.4", "1.8", "2.0", "3.0", "4.0", "TDI", "TFSI", "quattro", "FWD", "S", "RS",
        "30 TDI", "35 TDI", "40 TDI", "45 TDI", "50 TDI", 
        "30 TFSI", "35 TFSI", "40 TFSI", "45 TFSI", "55 TFSI",
        "45 TFSI quattro", "55 TFSI quattro", "40 TDI quattro", "50 TDI quattro",
        "A3 1.4 TFSI", "A4 2.0 TDI", "A6 3.0 TDI", "Q5 2.0 TDI", "S3", "RS6", "e-tron"
    ],
    "Volkswagen": [
        "1.0", "1.4", "1.5", "1.8", "2.0", "2.5", "3.0", "TSI", "TDI", "4Motion", "GTI", "R", "GTE", "BlueMotion", 
        "1.5 TSI", "2.0 TDI", "2.0 TSI", "1.4 TSI", "1.5 TSI", "1.8 TSI", "2.0 TDI 4Motion", "2.0 TSI 4Motion", "ID.3", "ID.4"
    ],
    "Porsche": [
        "2.0", "2.9", "3.0", "4.0", "Turbo", "S", "GTS", "4S",
        "911 Carrera", "911 Turbo", "718 Cayman", "Macan GTS", "Taycan Turbo S"
    ],

    # Japanese Brands
    "Toyota": [
        "1.2", "1.5", "1.8", "2.0", "2.5", "2.5L", "3.5", "Hybrid", "Dynamic Force", "AWD", "4WD", "TRD", "GR",
        "Corolla Hybrid", "Camry Hybrid", "RAV4 Hybrid", "Land Cruiser V8"
    ],
    "Honda": [
        "1.0", "1.5", "1.6", "1.8", "2.0", "2.4", "3.5", "i-VTEC", "Earth Dreams", "Type R", "AWD", "FWD",
        "Civic Type R", "Accord Hybrid", "CR-V AWD"
    ],

    # Korean Brands
    "Hyundai": [
        "1.6", "2.0", "2.5", "3.3", "MPI", "GDI", "T-GDI", "CRDi", "Smartstream", "N Line", "HTRAC", "AWD",
        "i30 N", "Sonata 2.5 Smartstream", "Santa Fe 2.2 CRDi"
    ],
    "Kia": [
        "1.6", "2.0", "2.5", "3.3", "MPI", "GDI", "CRDi", "GT-Line", "AWD", "Smartstream", "Stinger GT",
        "Sportage 2.0 MPI"
    ],

    # American Brands
    "Ford": [
        "1.5", "2.0", "2.3", "2.7", "3.0", "3.5", "5.0", "EcoBoost", "AWD", "FWD", "4WD", "ST", "Raptor",
        "Explorer 3.0 EcoBoost"
    ],
    "Tesla": [
        "Standard Range", "Long Range", "Performance", "Plaid", "AWD", "Dual Motor", "Tri Motor",
        "Model 3 Long Range", "Model Y Performance"
    ],

    # Chinese Brands
    "Chery": [
        "1.5T", "1.6T", "2.0T", "CVT", "DCT", "Turbo", "FWD", "AWD", "Tiggo 8 Pro"
    ],
    "Geely": [
        "1.5T", "1.8T", "2.0T", "TD", "TGDi", "MHEV", "PHEV", "AWD", "Coolray", "Tugella", "Monjaro"
    ],
    "Haval": [
        "1.5T", "2.0T", "DCT", "AWD", "FWD", "Jolion", "H6", "F7x", "Dargo"
    ],
    "Exeed": [
        "1.6TGDI", "2.0TGDI", "TXL", "VX", "LX", "AWD", "Luxury", "Flagship"
    ],
    "Changan": [
        "1.5T", "2.0T", "AWD", "FWD", "CS75 Plus", "UNI-K", "UNI-T"
    ],
    "Tank": [
        "2.0T", "3.0T", "4WD", "300", "500"
    ],
    "BYD": [
        "EV", "PHEV", "Blade Battery", "Han EV", "Tang EV", "Seal EV", "Dolphin EV"
    ],
    "Omoda": [
        "C5", "S5", "1.5T", "1.6T", "DCT", "AWD"
    ],
    "Jaecoo": [
        "J7", "1.6T", "AWD", "FWD"
    ],
    "Voyah": [
        "Free", "Dream", "EV", "EREV", "AWD"
    ],
    "Hongqi": [
        "2.0T", "3.0T", "EV", "H5", "HS5", "E-HS9"
    ],
    "NIO": ["AWD", "RWD", "Long Range", "Performance", "Standard Range", "Signature Edition"],
    "Jeep": ["Sport", "Latitude", "Limited", "Trailhawk", "Overland", "Summit", "Rubicon", "4xe"],
    "JAC": ["1.5T", "2.0T", "EV", "iEV", "MHEV", "FWD", "AWD"],
    "FAW": [
        "1.5T", "2.0T", "AWD", "Bestune T77", "Bestune T99"
    ]
}

from backend.models import Brand, BrandModification

def seed_brand_modifications(session):
    """Seed the BrandModification table"""
    logger.info("Starting brand modifications seeding process...")

    existing_mods_count = session.query(BrandModification).count()
    logger.info(f"Found {existing_mods_count} existing brand modifications")

    mods_added = 0
    brands_skipped = []

    for brand_name, modifications in BRAND_MODIFICATIONS.items():
        brand = session.query(Brand).filter(Brand.name == brand_name).first()
        if not brand:
            brands_skipped.append(brand_name)
            continue
        
        for mod_name in modifications:
            existing_mod = session.query(BrandModification).filter(
                BrandModification.brand_id == brand.id,
                BrandModification.name == mod_name
            ).first()
            if existing_mod:
                continue
            
            new_mod = BrandModification(
                name=mod_name,
                brand_id=brand.id,
                source='seed_script',
                created_at=datetime.utcnow()
            )
            session.add(new_mod)
            mods_added += 1

            if mods_added % 50 == 0:
                session.commit()
                logger.info(f"Added {mods_added} modifications so far...")

    session.commit()

    if brands_skipped:
        logger.warning(f"Skipped {len(brands_skipped)} brands not found in database: {', '.join(brands_skipped)}")

    logger.info(f"✅ Successfully added {mods_added} brand modifications")
    return mods_added, brands_skipped

if __name__ == "__main__":
    try:
        session = get_db_session()
        mods_added, brands_skipped = seed_brand_modifications(session)
        print(f"✅ Successfully added {mods_added} brand modifications")
        
        if brands_skipped:
            print(f"⚠️ Skipped {len(brands_skipped)} brands:")
            for brand in brands_skipped:
                print(f"  - {brand}")
        
        session.close()
    except Exception as e:
        logger.error(f"❌ Error seeding brand modifications: {e}")
        print(f"❌ Error seeding brand modifications: {e}")
        sys.exit(1)
