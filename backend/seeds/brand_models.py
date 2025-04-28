import sys
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Brand, BrandModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://cnauto:cnauto@localhost:5432/cnauto_db')
engine = create_engine(DATABASE_URL)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# Complete list of brands and models
BRAND_MODELS = {
    "Audi": ["A3", "A4", "A5", "A6", "A7", "A8", "Q3", "Q5", "Q7", "Q8", "e-tron", "RS3", "RS5", "RS6"],
    "Avatr": ["11", "12"],
    "BAIC": ["BJ40", "BJ80", "EU5", "EX5"],
    "BMW": ["1 Series", "2 Series", "3 Series", "4 Series", "5 Series", "7 Series", "X1", "X3", "X5", "X6", "i4", "iX"],
    "Buick": ["Encore", "Envision", "Enclave", "Regal", "LaCrosse"],
    "BYD": ["Tang", "Song", "Han", "Dolphin", "Seal", "Atto 3"],
    "Cadillac": ["CT4", "CT5", "XT4", "XT5", "XT6", "Escalade"],
    "Changan": ["CS35", "CS55", "CS75", "UNI-T", "UNI-K"],
    "Chery": ["Tiggo 4", "Tiggo 7", "Tiggo 8", "Arrizo 5", "Arrizo 8"],
    "Chevrolet": ["Spark", "Malibu", "Trax", "Trailblazer", "Equinox", "Tahoe", "Silverado"],
    "Citroen": ["C3", "C4", "C5", "C5 Aircross", "Berlingo"],
    "Denza": ["D9", "N7"],
    "Dongfeng": ["Aeolus AX7", "Joyear X5", "Fengshen E70"],
    "Exeed": ["TXL", "VX", "LX"],
    "FAW": ["Bestune T77", "Bestune T99"],
    "Ford": ["Focus", "Kuga", "Escape", "Edge", "Explorer", "F-150", "Mustang"],
    "Forthing": ["T5 Evo", "S500"],
    "GAC": ["GS4", "GS8", "Aion S", "Aion V"],
    "Geely": ["Coolray", "Atlas", "Monjaro", "Tugella", "Emgrand"],
    "Great Wall": ["Poer", "Tank 300", "Tank 500"],
    "Haval": ["Jolion", "H6", "F7", "Dargo"],
    "HiPhi": ["X", "Z", "Y"],
    "Honda": ["Civic", "Accord", "CR-V", "HR-V", "Pilot"],
    "Hongqi": ["H5", "H7", "HS5", "HS7", "E-HS9"],
    "Huawei": ["Aito M5", "Aito M7"],
    "Hyundai": ["i20", "Elantra", "Sonata", "Tucson", "Santa Fe", "Palisade", "Kona"],
    "Infiniti": ["Q50", "Q60", "QX50", "QX60", "QX80"],
    "Jaguar": ["XE", "XF", "F-Pace", "E-Pace", "I-Pace"],
    "Jetour": ["X70", "X90"],
    "Jetta": ["VS5", "VS7", "VA3"],
    "Jishi": ["01"],
    "Kia": ["Rio", "Ceed", "Cerato", "Sportage", "Sorento", "EV6", "Seltos"],
    "Land Rover": ["Defender", "Discovery", "Range Rover", "Range Rover Sport", "Evoque"],
    "Leamotor": ["S01", "C01"],
    "Lexus": ["UX", "NX", "RX", "GX", "LX", "IS", "ES", "LS"],
    "Lincoln": ["Corsair", "Nautilus", "Aviator", "Navigator"],
    "LiXiang": ["L7", "L8", "L9"],
    "Lotus": ["Eletre", "Emira"],
    "Lynk & Co": ["01", "02", "03", "05", "06", "09"],
    "Mazda": ["Mazda3", "Mazda6", "CX-30", "CX-5", "CX-9"],
    "Mercedes-Benz": ["A-Class", "C-Class", "E-Class", "S-Class", "GLA", "GLC", "GLE", "GLS", "EQC", "EQS"],
    "MG": ["ZS", "HS", "5 EV", "MG4", "MG5", "MG6"],
    "Mini": ["Cooper", "Countryman", "Clubman", "Electric"],
    "Mitsubishi": ["ASX", "Outlander", "Pajero Sport", "Eclipse Cross"],
    "Neta": ["V", "U", "S", "GT"],
    "Nio": ["ES6", "ES7", "ES8", "EC6", "ET5", "ET7"],
    "Nissan": ["Juke", "Qashqai", "X-Trail", "Murano", "Pathfinder", "Leaf", "GT-R"],
    "Peugeot": ["208", "2008", "308", "3008", "408", "508"],
    "Polestar": ["2", "3"],
    "Porsche": ["911", "Cayenne", "Macan", "Taycan", "Panamera"],
    "Skoda": ["Fabia", "Octavia", "Superb", "Karoq", "Kodiaq", "Enyaq"],
    "Smart": ["ForTwo", "ForFour", "#1", "#3"],
    "Tank": ["300", "500"],
    "Tesla": ["Model 3", "Model Y", "Model S", "Model X", "Cybertruck"],
    "Toyota": ["Corolla", "Camry", "RAV4", "Highlander", "Land Cruiser", "Yaris", "C-HR", "Hilux"],
    "Venucia": ["D60", "T60", "Star"],
    "Volkswagen": ["Polo", "Golf", "Tiguan", "Touareg", "Passat", "Arteon", "ID.3", "ID.4"],
    "Volvo": ["XC40", "XC60", "XC90", "S60", "S90", "V60", "EX90"],
    "Voyah": ["Free", "Dreamer"],
    "Wuling": ["Hongguang Mini EV", "Victory", "Asta"],
    "Xiaomi": ["SU7"],
    "Xpeng": ["G3", "P5", "P7", "G9"],
    "NIO": ["ES6", "ES7", "ES8", "EC6", "ET5", "ET7"],
    "Jeep": ["Renegade", "Compass", "Cherokee", "Grand Cherokee", "Wrangler", "Gladiator", "Wagoneer"],
    "JAC": ["JS4", "JS6", "S4", "S7", "iEV7S", "E10X"],
    "Zeekr": ["001", "X", "009"]
}

def seed_brand_models():
    session = Session()
    try:
        brands = session.query(Brand).all()
        for brand in brands:
            if brand.name in BRAND_MODELS:
                models_data = BRAND_MODELS[brand.name]
                for model_name in models_data:
                    existing = session.query(BrandModel).filter_by(
                        name=model_name,
                        brand_id=brand.id
                    ).first()
                    if not existing:
                        is_multi_word = len(model_name.split()) > 1
                        brand_model = BrandModel(
                            name=model_name,
                            brand_id=brand.id,
                            is_multi_word=is_multi_word,
                            source="seed_script"
                        )
                        session.add(brand_model)
                        logger.info(f"Added model '{model_name}' for brand '{brand.name}'")
        session.commit()
        logger.info(f"✅ Successfully seeded brand models")
    except Exception as e:
        session.rollback()
        logger.error(f"Error seeding brand models: {str(e)}")
    finally:
        Session.remove()

if __name__ == "__main__":
    logger.info("🚀 Starting brand models seed script")
    seed_brand_models()
    logger.info("✅ Brand models seeding completed")
