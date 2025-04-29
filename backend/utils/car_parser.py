"""
Car model parser utility for processing car info in [Brand] [Model] [Modification] format
and converting it to [Brand] [Model] [Modification] [Trim] format.
"""

import requests
import json
import os
import re
from flask import current_app

# Configure logging
from utils.file_logger import get_module_logger
logger = get_module_logger(__name__)

# Keep track of new trims and modifications for database persistence
NEW_TRIMS = []
NEW_MODIFICATIONS = []

# Cache for car API results to minimize external API calls
API_RESULTS_CACHE = {}

def save_new_trims_to_db(db_session=None):
    """
    Save newly discovered trims to the database for future reference.
    
    Args:
        db_session: Optional SQLAlchemy session to use for database operations
    """
    if not NEW_TRIMS:
        return
    
    if not db_session:
        logger.warning("⚠️ No database session provided to save_new_trims_to_db")
        return
    
    for trim_data in NEW_TRIMS:
        brand_name = trim_data.get('brand')
        trim_name = trim_data.get('trim')
        source = trim_data.get('source', 'auto_detected')
        
        if not brand_name or not trim_name:
            continue
            
        try:
            # Find the brand
            brand = db_session.query(Brand).filter(Brand.name == brand_name).first()
            if not brand:
                logger.warning(f"⚠️ Cannot save trim: Brand '{brand_name}' not found")
                continue
                
            # Check if this trim already exists for this brand
            existing_trim = db_session.query(BrandTrim).filter(
                BrandTrim.brand_id == brand.id,
                BrandTrim.name == trim_name
            ).first()
            
            if not existing_trim:
                # Create new brand trim
                new_trim = BrandTrim(
                    name=trim_name,
                    brand_id=brand.id,
                    source=source
                )
                db_session.add(new_trim)
                db_session.commit()
                logger.info(f"✅ New trim added: {trim_name} for {brand_name}")
            else:
                logger.debug(f"ℹ️ Trim already exists: {trim_name} for {brand_name}")
        except Exception as e:
            logger.error(f"❌ Error saving trim {trim_name} for {brand_name}: {e}")
    
    # Clear the list after processing
    NEW_TRIMS.clear()

def save_new_modifications_to_db(db_session=None):
    """
    Save newly discovered modifications to the database for future reference.
    
    Args:
        db_session: Optional SQLAlchemy session to use for database operations
    """
    if not NEW_MODIFICATIONS:
        return
    
    if not db_session:
        logger.warning("⚠️ No database session provided to save_new_modifications_to_db")
        return
    
    for mod_data in NEW_MODIFICATIONS:
        brand_name = mod_data.get('brand')
        mod_name = mod_data.get('modification')
        source = mod_data.get('source', 'auto_detected')
        
        if not brand_name or not mod_name:
            continue
            
        try:
            # Find the brand
            brand = db_session.query(Brand).filter(Brand.name == brand_name).first()
            if not brand:
                logger.warning(f"⚠️ Cannot save modification: Brand '{brand_name}' not found")
                continue
                
            # Check if this modification already exists for this brand
            existing_mod = db_session.query(BrandModification).filter(
                BrandModification.brand_id == brand.id,
                BrandModification.name == mod_name
            ).first()
            
            if not existing_mod:
                # Create new brand modification
                new_mod = BrandModification(
                    name=mod_name,
                    brand_id=brand.id,
                    source=source
                )
                db_session.add(new_mod)
                db_session.commit()
                logger.info(f"✅ New modification added: {mod_name} for {brand_name}")
            else:
                logger.debug(f"ℹ️ Modification already exists: {mod_name} for {brand_name}")
        except Exception as e:
            logger.error(f"❌ Error saving modification {mod_name} for {brand_name}: {e}")
    
    # Clear the list after processing
    NEW_MODIFICATIONS.clear()

def get_brand_trims(brand_name, db_session=None):
    """
    Get all trims associated with a brand from the database
    
    Args:
        brand_name (str): The brand name
        db_session: SQLAlchemy session
        
    Returns:
        list: List of trim names for the brand
        
    Raises:
        ValueError: If db_session is not provided
    """
    if not db_session:
        raise ValueError("Database session is required to get brand trims")
    
    from backend.models import Brand, BrandTrim
    try:
        # Find the brand
        brand = db_session.query(Brand).filter(Brand.name == brand_name).first()
        if not brand:
            logger.warning(f"Brand not found: {brand_name}")
            return ["Standard"]  # Return default trim
            
        # Get all trims for this brand
        trims = db_session.query(BrandTrim).filter(BrandTrim.brand_id == brand.id).all()
        trim_names = [trim.name for trim in trims]
        
        # Always include "Standard" as a fallback trim
        if "Standard" not in trim_names:
            trim_names.append("Standard")
            
        return trim_names
    except Exception as e:
        logger.error(f"Error getting trims for brand {brand_name}: {str(e)}")
        raise

def get_all_brands_with_synonyms(db_session=None):
    """
    Get all brands and their synonyms from the database
    
    Args:
        db_session: SQLAlchemy session
        
    Returns:
        list: List of brand names and their synonyms
        
    Raises:
        ValueError: If db_session is not provided
    """
    if not db_session:
        raise ValueError("Database session is required to get brands with synonyms")
    
    try:
        # Try to get brands from the database
        from backend.models import Brand, BrandSynonym
        
        brands = []
        
        # Query all brands
        brand_objects = db_session.query(Brand).all()
        for brand in brand_objects:
            brands.append(brand.name)
            
            # Get synonyms for this brand
            try:
                synonyms = db_session.query(BrandSynonym).filter(BrandSynonym.brand_id == brand.id).all()
                for synonym in synonyms:
                    brands.append(synonym.name)
            except Exception as e:
                logger.error(f"Error getting synonyms for brand {brand.name}: {str(e)}")
                
        return brands
    except Exception as e:
        logger.error(f"Error getting brands with synonyms: {str(e)}")
        raise

def get_brand_models(brand_name, db_session=None):
    """
    Get all models for a brand from the database
    
    Args:
        brand_name (str): Brand name
        db_session: SQLAlchemy session
        
    Returns:
        list: List of model names for the brand
        
    Raises:
        ValueError: If db_session is not provided
    """
    if not db_session:
        raise ValueError("Database session is required to get brand models")
    
    try:
        # Try to get models from the database
        from backend.models import Brand, BrandModel
        
        # Find the brand first
        brand = db_session.query(Brand).filter(Brand.name == brand_name).first()
        if not brand:
            logger.warning(f"Brand not found: {brand_name}")
            return []
        
        # Get all models for this brand
        models = db_session.query(BrandModel).filter(BrandModel.brand_id == brand.id).all()
        return [model.name for model in models]
    except Exception as e:
        logger.error(f"Error getting models for brand {brand_name}: {str(e)}")
        raise

def get_brand_modifications(brand_name, db_session=None):
    """
    Get all known modifications for a brand.
    
    Args:
        brand_name (str): The brand name
        db_session: SQLAlchemy session
        
    Returns:
        list: List of modification names
        
    Raises:
        ValueError: If db_session is not provided
    """
    if not db_session:
        raise ValueError("Database session is required to get brand modifications")
        
    try:
        from backend.models import Brand, BrandModification
        
        # Get brand
        brand = db_session.query(Brand).filter(Brand.name == brand_name).first()
        if not brand:
            logger.warning(f"Brand not found: {brand_name}")
            return []
            
        # Get modifications for this brand
        modifications = db_session.query(BrandModification).filter(BrandModification.brand_id == brand.id).all()
        return [mod.name for mod in modifications]
    except Exception as e:
        logger.error(f"Error getting modifications for brand {brand_name}: {str(e)}")
        raise

def save_new_model_to_db(brand_name, model_name, db_session=None):
    """
    Save newly discovered model to the database for future reference.
    
    Args:
        brand_name (str): The brand name
        model_name (str): The model name
        db_session: Optional SQLAlchemy session to use for database operations
        
    Returns:
        bool: True if model was added, False otherwise
    """
    if not db_session:
        db_session = db.session
    
    # Do nothing if empty or too short model name
    if not model_name or len(model_name) < 2:
        return False
    
    try:
        # Find brand
        brand = db_session.query(Brand).filter(Brand.name == brand_name).first()
        if not brand:
            logger.warning(f"Cannot save model: Brand '{brand_name}' not found")
            return False
        
        # Check if model already exists for this brand
        existing = db_session.query(BrandModel).filter(
            BrandModel.name == model_name,
            BrandModel.brand_id == brand.id
        ).first()
        
        if not existing:
            # Create new model
            is_multi_word = len(model_name.split()) > 1
            brand_model = BrandModel(
                name=model_name,
                brand_id=brand.id,
                is_multi_word=is_multi_word,
                source="auto_detected"
            )
            db_session.add(brand_model)
            db_session.commit()
            logger.info(f"Added new model '{model_name}' for brand '{brand_name}'")
            return True
    except Exception as e:
        logger.error(f"Error saving model to DB: {str(e)}")
        if db_session:
            db_session.rollback()
    
    return False

def find_known_trim(brand, text, db_session=None):
    """
    Check if text contains a known trim for the given brand.
    Search is case-insensitive.
    
    Args:
        brand (str): Car brand
        text (str): Text to search in
        db_session: Optional database session
        
    Returns:
        str or None: Found trim string or None
    """
    if not db_session:
        try:
            from flask import current_app
            db_session = current_app.extensions['sqlalchemy'].db.session
        except (ImportError, RuntimeError):
            # Outside of Flask context, try to create a new session
            from backend.database import Session
            db_session = Session()
    
    # Get brand ID
    try:
        brand_obj = db_session.query(Brand).filter(Brand.name == brand).first()
        if not brand_obj:
            return None
            
        # Get all trims for this brand
        trims = db_session.query(BrandTrim).filter(BrandTrim.brand_id == brand_obj.id).all()
        if not trims:
            return None
            
        # Sort trims by length (longest first) to match more specific trims before generic ones
        trims_sorted = sorted(trims, key=lambda x: len(x.name), reverse=True)
        
        # Check each trim
        for trim in trims_sorted:
            # Check against word boundaries (e.g., "Sport" shouldn't match "SportBack")
            pattern = r'\b' + re.escape(trim.name) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return trim.name
                
        return None
    except Exception as e:
        logger.error(f"Error finding trim: {e}")
        return None

def find_known_modification(brand, modification_text, db_session=None):
    """
    Check if the modification text matches a known modification for the brand.
    
    Args:
        brand (str): The brand name
        modification_text (str): The modification text to check
        db_session: Optional SQLAlchemy session to use for queries
        
    Returns:
        str: Found modification or None
    """
    # Skip database check if no session is provided or modification is empty
    if not db_session or not modification_text:
        return None
    
    try:
        # Get all known modifications for this brand
        brand_mods = get_brand_modifications(brand, db_session)
        
        # First check for exact matches
        for mod in brand_mods:
            if mod.lower() == modification_text.lower():
                return mod
                
        # Then check if any modification is contained in the text
        for mod in brand_mods:
            if mod.lower() in modification_text.lower():
                return mod
                
        # If no direct match, check cars table for similar modifications
        cars_with_mods = db_session.query(Car).join(Car.brand).filter(
            Brand.name == brand,
            Car.modification.isnot(None),
            Car.modification != ''
        ).all()
        
        # Extract unique modifications
        possible_mods = set()
        for car in cars_with_mods:
            if car.modification and car.modification.strip():
                possible_mods.add(car.modification.strip())
        
        # Check if any known modification appears in the text
        for mod in possible_mods:
            if mod.lower() in modification_text.lower():
                return mod
                
    except Exception as e:
        logger.error(f"Error finding known modification for {brand}: {e}")
    
    return None

def check_trim_carquery(brand, model, trim_candidate):
    """
    Check if trim candidate exists in CarQuery API for the given brand and model.
    
    Args:
        brand (str): Car brand
        model (str): Car model
        trim_candidate (str): Potential trim to check
        
    Returns:
        bool: True if trim is confirmed, False otherwise
    """
    cache_key = f"{brand.lower()}_{model.lower()}"
    
    # Check cache first
    if cache_key in API_RESULTS_CACHE.get('carquery', {}):
        trims = API_RESULTS_CACHE['carquery'][cache_key]
    else:
        try:
            url = f"https://www.carqueryapi.com/api/0.3/?cmd=getTrims&make={brand.lower()}&model={model.lower()}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                trims = data.get('Trims', [])
                
                # Cache the results
                if 'carquery' not in API_RESULTS_CACHE:
                    API_RESULTS_CACHE['carquery'] = {}
                API_RESULTS_CACHE['carquery'][cache_key] = trims
            else:
                logger.warning(f"CarQuery API returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error querying CarQuery API: {e}")
            return False
    
    # Check if trim candidate exists in results
    for car in trims:
        model_trim = car.get('model_trim', '').lower()
        if trim_candidate.lower() in model_trim:
            logger.info(f"✅ Trim confirmed in CarQuery: {model_trim}")
            return True
    
    return False

def check_trim_carapi(brand, model, trim_candidate):
    """
    Check if trim candidate exists in CarAPI for the given brand and model.
    
    Args:
        brand (str): Car brand
        model (str): Car model
        trim_candidate (str): Potential trim to check
        
    Returns:
        bool: True if trim is confirmed, False otherwise
    """
    # Get API credentials from Flask app config
    try:
        from flask import current_app
        carapi_key = current_app.config.get('CARAPI_API_KEY', os.getenv("CARAPI_API_KEY", ""))
        carapi_secret = current_app.config.get('CARAPI_API_SECRET', os.getenv("CARAPI_API_SECRET", ""))
    except (ImportError, RuntimeError):
        # Fallback to environment variables if not in Flask context
        carapi_key = os.getenv("CARAPI_API_KEY", "")
        carapi_secret = os.getenv("CARAPI_API_SECRET", "")
        
    if not carapi_key or not carapi_secret:
        logger.warning("⚠️ CARAPI_API_KEY or CARAPI_API_SECRET not set in config/environment")
        return False
    
    cache_key = f"{brand.lower()}_{model.lower()}"
    
    # Check cache first
    if cache_key in API_RESULTS_CACHE.get('carapi', {}):
        cars = API_RESULTS_CACHE['carapi'][cache_key]
    else:
        try:
            # First get an access token using key and secret
            auth_url = "https://carapi.app/api/auth/login"
            auth_data = {
                "api_token": carapi_key,
                "api_secret": carapi_secret
            }
            auth_response = requests.post(auth_url, json=auth_data, timeout=5)
            
            if auth_response.status_code != 200:
                logger.warning(f"CarAPI authentication failed with status {auth_response.status_code}")
                return False
                
            # Extract access token from response
            auth_data = auth_response.json()
            access_token = auth_data.get('access_token')
            
            if not access_token:
                logger.warning("CarAPI did not return an access token")
                return False
            
            # Now use the access token to query the API
            url = f"https://carapi.app/api/v1/trims?make={brand.lower()}&model={model.lower()}"
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                cars = data.get('data', [])
                
                # Cache the results
                if 'carapi' not in API_RESULTS_CACHE:
                    API_RESULTS_CACHE['carapi'] = {}
                API_RESULTS_CACHE['carapi'][cache_key] = cars
            else:
                logger.warning(f"CarAPI returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error querying CarAPI: {e}")
            return False
    
    # Check if trim candidate exists in results
    for car in cars:
        model_trim = car.get('trim', '').lower()
        if trim_candidate.lower() in model_trim:
            logger.info(f"✅ Trim confirmed in CarAPI: {model_trim}")
            return True
    
    return False

def parse_car_info(car_data, db_session):
    """
    Parse car information from input string
    
    Example input: "BMW X5 xDrive30d M Sport"
    Output:
    {
        "brand": "BMW",
        "model": "X5",
        "modification": "xDrive30d",
        "trim": "M Sport",
        "engine": {
            "displacement": "3.0",
            "power_hp": None,
            "type": "diesel",
            "drive": "xdrive",
            "transmission": None,
            "engine_text": "xDrive30d"
        }
    }
    
    Args:
        car_data (str): Car data string
        db_session: SQLAlchemy session
        
    Returns:
        dict: Car information with brand, model, modification, trim, and engine info
        
    Raises:
        ValueError: If db_session is not provided
    """
    if not db_session:
        raise ValueError("Database session is required to parse car info")
        
    result = {
        "brand": None,
        "model": None,
        "modification": None,
        "trim": None,
        "engine": None
    }
    
    # Step 1: Extract brand (longest matching brand first)
    all_brands = get_all_brands_with_synonyms(db_session)
    sorted_brands = sorted(all_brands, key=len, reverse=True)
    found_brand = None
    brand_end_index = 0
    for brand in sorted_brands:
        brand_pattern = r'\b' + re.escape(brand) + r'\b'
        match = re.search(brand_pattern, car_data, re.IGNORECASE)
        if match:
            found_brand = brand
            brand_end_index = match.end()
            break
    
    if not found_brand:
        # Try fallback method: use first word as brand
        words = car_data.split()
        if words:
            found_brand = words[0]
            brand_end_index = len(found_brand)
            
            # Add this brand to the database if it doesn't exist
            create_or_get_brand(found_brand, db_session)
    
    result["brand"] = found_brand
    
    if not found_brand:
        # Can't parse further without a brand
        return result
    
    # Get the rest of the text after the brand for further processing
    remaining_text = car_data[brand_end_index:].strip()
    if not remaining_text:
        return result
    
    # Step 2: Identify engine info from the remaining text
    engine_info = extract_engine_info(remaining_text)
    result["engine"] = engine_info
    
    # Step 3: Extract model (based on the brand)
    # Get models for this brand from DB
    try:
        models = get_brand_models(found_brand, db_session)
        
        # Sort models by length (longer models first) for more specific matches
        sorted_models = sorted(models, key=len, reverse=True)
        
        # Split into multi-word and single-word models
        multi_word_models = [m for m in sorted_models if ' ' in m]
        single_word_models = [m for m in sorted_models if ' ' not in m]
        
        # Try to find model - first try multi-word models, then single-word
        found_model = None
        model_end_index = 0
        
        # First, try matching multi-word models with exact boundary match
        for model in multi_word_models:
            model_pattern = r'\b' + re.escape(model) + r'\b'
            match = re.search(model_pattern, remaining_text, re.IGNORECASE)
            if match:
                found_model = model
                model_end_index = brand_end_index + match.end()
                break
        
        # If no multi-word model found, try single-word models
        if not found_model:
            for model in single_word_models:
                model_pattern = r'\b' + re.escape(model) + r'\b'
                match = re.search(model_pattern, remaining_text, re.IGNORECASE)
                if match:
                    found_model = model
                    model_end_index = brand_end_index + match.end()
                    break
        
        # If still no model found, use first word in remaining text as potential model
        if not found_model:
            words = remaining_text.split()
            if words:
                found_model = words[0]
                model_end_index = brand_end_index + remaining_text.find(words[0]) + len(words[0])
                
                # Add this model to the database if it doesn't exist
                create_or_get_model(found_brand, found_model, db_session)
        
        result["model"] = found_model
        
        if not found_model:
            # Can't parse further without a model
            return result
        
        # Get modification text after model
        mod_text_start = None
        if found_model:
            # Try to match model in remaining_text and get its end position
            model_pattern = r'\b' + re.escape(found_model) + r'\b'
            match = re.search(model_pattern, remaining_text, re.IGNORECASE)
            if match:
                mod_text_start = match.end()
        if mod_text_start is not None:
            modification_text = remaining_text[mod_text_start:].strip()
        else:
            modification_text = car_data[model_end_index:].strip()
        if not modification_text:
            return result
        
        # Step 4 & 5: Normalize the car data (extract trim and modification)
        normalized = normalize_car(found_brand, found_model, modification_text, db_session)
        result.update(normalized)
        
        return result
    except Exception as e:
        logger.error(f"Error parsing car info: {str(e)}")
        raise

def normalize_car(brand, model, modification_text, db_session):
    """
    Normalize car data by extracting trim and modification based on brand-specific knowledge
    
    Args:
        brand (str): Car brand
        model (str): Car model
        modification_text (str): Modification text
        db_session: SQLAlchemy session
        
    Returns:
        dict: Normalized car data with brand, model, modification, trim, and engine
    """
    if not db_session:
        raise ValueError("Database session is required to normalize car data")
    
    result = {
        "brand": brand,
        "model": model,
        "modification": modification_text.strip(),
        "trim": "Standard"
    }
    
    # Remove anything in parentheses (e.g., (версия Ruiyi))
    mod_text = re.sub(r'\([^)]*\)', '', modification_text).strip()

    # Get all known trims for this brand
    brand_trims = get_brand_trims(brand, db_session)
    sorted_trims = sorted(brand_trims, key=len, reverse=True)

    # Find trim first - prioritize multi-word trims
    trim = None
    # Try to match multi-word trims first (using exact match with boundaries)
    for trim_candidate in sorted_trims:
        if ' ' in trim_candidate:
            if re.search(r'\b' + re.escape(trim_candidate) + r'\b', mod_text, re.IGNORECASE):
                trim = trim_candidate
                # Remove the trim from the modification text
                mod_text = re.sub(r'\b' + re.escape(trim_candidate) + r'\b', '', mod_text, flags=re.IGNORECASE).strip()
                break

    # If no multi-word trim found, try to match single-word trims
    if not trim:
        for trim_candidate in sorted_trims:
            if ' ' not in trim_candidate and len(trim_candidate) > 1:
                if re.search(r'\b' + re.escape(trim_candidate) + r'\b', mod_text, re.IGNORECASE):
                    trim = trim_candidate
                    # Remove the trim from the modification text
                    mod_text = re.sub(r'\b' + re.escape(trim_candidate) + r'\b', '', mod_text, flags=re.IGNORECASE).strip()
                    break

    # If no trim was found, check the last word as a potential trim
    if not trim:
        words = mod_text.split()
        if len(words) > 1:
            # Check if the last word or last two words form a known trim
            last_word = words[-1]
            if find_known_trim(brand, last_word, db_session):
                trim = last_word
                mod_text = ' '.join(words[:-1]).strip()
            elif len(words) > 2:
                last_two_words = ' '.join(words[-2:])
                if find_known_trim(brand, last_two_words, db_session):
                    trim = last_two_words
                    mod_text = ' '.join(words[:-2]).strip()

    # If still no trim found, use "Standard"
    if not trim:
        trim = "Standard"

    # After extracting trim, normalize modification (e.g., '2.0TSI' -> '2.0 TSI')
    def normalize_mod(mod):
        # Insert space between number and letters (e.g., 2.0TSI -> 2.0 TSI)
        mod = re.sub(r'(\d\.\d)([A-Za-z])', r'\1 \2', mod)
        mod = re.sub(r'(\d)([A-Za-z])', r'\1 \2', mod)
        mod = re.sub(r'([A-Za-z])([0-9])', r'\1 \2', mod)
        return mod.strip()
    mod_text = normalize_mod(mod_text)

    # Everything else is considered the modification (clean up extra spaces)
    mod_text = re.sub(r'\s+', ' ', mod_text).strip()

    # Return normalized car info
    result["modification"] = mod_text
    result["trim"] = trim
    
    return result

def save_new_brand_to_db(brand_name, db_session=None):
    """Save a newly discovered brand to the database."""
    if not db_session:
        db_session = db.session
    
    try:
        # Check if brand already exists
        existing = db_session.query(Brand).filter(Brand.name == brand_name).first()
        if not existing:
            # Get default country (can be updated by admin later)
            default_country = db_session.query(Country).first()
            if not default_country:
                logger.warning("Cannot save brand: No countries available in database")
                return False
            
            # Create a slug from the brand name
            slug = brand_name.lower().replace(' ', '-')
            
            # Create the new brand
            new_brand = Brand(
                name=brand_name,
                slug=slug,
                country=default_country,
                source="auto_detected"
            )
            db_session.add(new_brand)
            db_session.commit()
            logger.info(f"Added new brand: {brand_name}")
            return True
    except Exception as e:
        logger.error(f"Error saving brand to DB: {str(e)}")
        if db_session:
            db_session.rollback()
    
    return False

def create_or_get_brand(brand_name, db_session=None):
    """
    Create a new brand if it doesn't exist in the database, or get an existing one.
    
    Args:
        brand_name (str): Brand name
        db_session: SQLAlchemy session
        
    Returns:
        The brand object (real or stub depending on environment)
    """
    try:
        if db_session:
            from backend.models import Brand
            brand = db_session.query(Brand).filter(Brand.name == brand_name).first()
            if not brand:
                # Create new brand
                brand = Brand(name=brand_name, slug=brand_name.lower())
                db_session.add(brand)
                db_session.commit()
            return brand
        else:
            # We're in a test environment or don't have a session
            # Just return a stub object with the name and id properties
            class StubBrand:
                def __init__(self, name):
                    self.name = name
                    self.id = 1  # Dummy ID
            return StubBrand(brand_name)
    except Exception as e:
        logger.error(f"Error creating/getting brand: {str(e)}")
        # Return a stub brand as fallback
        class StubBrand:
            def __init__(self, name):
                self.name = name
                self.id = 1  # Dummy ID
        return StubBrand(brand_name)

def create_or_get_model(brand_name, model_name, db_session=None):
    """
    Create a new model if it doesn't exist in the database, or get an existing one.
    
    Args:
        brand_name (str): Brand name
        model_name (str): Model name
        db_session: SQLAlchemy session
        
    Returns:
        The model object (real or stub depending on environment)
    """
    try:
        if db_session:
            # Get brand first
            brand = create_or_get_brand(brand_name, db_session)
            
            from backend.models import BrandModel
            model = db_session.query(BrandModel).filter(
                BrandModel.brand_id == brand.id,
                BrandModel.name == model_name
            ).first()
            
            if not model:
                # Create new model
                model = BrandModel(
                    name=model_name, 
                    brand_id=brand.id,
                    is_multi_word=' ' in model_name
                )
                db_session.add(model)
                db_session.commit()
            return model
        else:
            # We're in a test environment or don't have a session
            # Just return a stub object
            class StubModel:
                def __init__(self, name, brand_name):
                    self.name = name
                    self.brand_name = brand_name
            return StubModel(model_name, brand_name)
    except Exception as e:
        logger.error(f"Error creating/getting model: {str(e)}")
        # Return a stub model as fallback
        class StubModel:
            def __init__(self, name, brand_name):
                self.name = name
                self.brand_name = brand_name
        return StubModel(model_name, brand_name)

def extract_engine_info(text):
    """
    Extract engine information from text
    
    Args:
        text (str): Text containing engine information
        
    Returns:
        dict: Engine data with displacement, power_hp, type, drive, transmission
    """
    engine_data = {
        "displacement": None,
        "power_hp": None,
        "type": None,
        "drive": None,
        "transmission": None,
        "engine_text": text
    }
    
    # Extract displacement (e.g., 1.6T, 2.0, 2.5L, 77.4 kWh)
    displacement_patterns = [
        r'\b(\d+\.\d+\s?TSI)\b',              # 2.0 TSI
        r'\b(\d+\.\d+\s?TDI)\b',              # 2.0 TDI
        r'\b(\d+\.\d+\s?TFSI)\b',             # 2.0 TFSI
        r'\b(\d+\.\d+)[T](?!\w)\b',           # 2.0T but not 2.0TSI
        r'\b(\d+\.\d+)\s?[L](?!\w)\b',        # 2.5L but not 2.5LSA
        r'\b(\d+\.\d+)\s?(?:литра|л)(?!\w)\b',  # 2.0 литра, 1.6л
        r'\b(\d+\.\d+)\s?(?:kWh|kwh|кВтч)\b', # 77.4 kWh
        r'\b(\d+\.\d+)\b'                     # 2.0, 1.6 (plain number, lowest priority)
    ]
    
    for pattern in displacement_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            engine_data["displacement"] = match.group(0)
            break
    
    # Extract power (e.g., 150 hp, 110 л.с.)
    power_patterns = [
        r'\b(\d+)\s?(?:hp|л\.с\.|лс)\b',    # 150 hp, 110 л.с.
        r'\b(\d+)\s?(?:HP|ЛС)\b'           # 220 HP, 180 ЛС
    ]
    
    for pattern in power_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            engine_data["power_hp"] = int(match.group(1))
            break
    
    # Determine engine type
    if re.search(r'\b(?:гибрид|hybrid)\b', text, re.IGNORECASE):
        engine_data["type"] = "hybrid"
    elif re.search(r'\b(?:электр|electric|EV)\b', text, re.IGNORECASE) or "kWh" in text:
        engine_data["type"] = "electric"
    elif re.search(r'\b(?:дизель|diesel|TDI|xDrive\d+d)\b', text, re.IGNORECASE):
        engine_data["type"] = "diesel"
    elif re.search(r'\b(?:бензин|gasoline|petrol|TSI|TFSI)\b', text, re.IGNORECASE) or re.search(r'\b\d+\.\d+T\b', text, re.IGNORECASE):
        engine_data["type"] = "gasoline"
    
    # Determine drive type
    if re.search(r'\b(?:4WD|4x4|AWD|4Motion|полный привод|all wheel drive)\b', text, re.IGNORECASE):
        engine_data["drive"] = "all_wheel_drive"
    elif re.search(r'\b(?:RWD|задний привод|rear wheel drive)\b', text, re.IGNORECASE):
        engine_data["drive"] = "rear_wheel_drive"
    elif re.search(r'\b(?:FWD|передний привод|front wheel drive)\b', text, re.IGNORECASE):
        engine_data["drive"] = "front_wheel_drive"
    elif re.search(r'\bquattro\b', text, re.IGNORECASE):
        engine_data["drive"] = "quattro"
    elif re.search(r'\bxDrive', text, re.IGNORECASE):
        engine_data["drive"] = "xdrive"
    elif re.search(r'\bE-Four\b', text, re.IGNORECASE):
        engine_data["drive"] = "e_four"
    
    # Determine transmission
    if re.search(r'\b(?:DSG|S-?tronic)\b', text, re.IGNORECASE):
        engine_data["transmission"] = "dsg"
    elif re.search(r'\b(?:CVT|вариатор)\b', text, re.IGNORECASE):
        engine_data["transmission"] = "cvt"
    elif re.search(r'\b(?:АКПП|автомат|automatic)\b', text, re.IGNORECASE):
        engine_data["transmission"] = "automatic"
    elif re.search(r'\b(?:МКПП|механика|manual)\b', text, re.IGNORECASE):
        engine_data["transmission"] = "manual"
    elif re.search(r'\b(?:PDK)\b', text, re.IGNORECASE):
        engine_data["transmission"] = "pdk"
    elif re.search(r'\b(?:DCT)\b', text, re.IGNORECASE):
        engine_data["transmission"] = "dct"
    
    return engine_data

def get_db_session():
    try:
        from flask import current_app
        return current_app.extensions['sqlalchemy'].db.session
    except (ImportError, RuntimeError):
        # Outside of Flask context, try to create a new session
        from backend.database import Session
        return Session()
