"""
Car model parser utility for processing car info in [Brand] [Model] [Modification] format
and converting it to [Brand] [Model] [Modification] [Trim] format.
"""

import requests
import json
import os
from flask import current_app
from models import db, Brand, BrandSynonym, Car

# Configure logging
from utils.file_logger import get_module_logger
logger = get_module_logger(__name__)

# Keep track of new trims for database persistence
NEW_TRIMS = []

# Cache for car API results to minimize external API calls
API_RESULTS_CACHE = {}

def save_new_trims_to_db(db_session=None):
    """
    Save newly discovered trims to the database for future reference.
    This could be implemented as a separate table or added to existing Brand data.
    
    Args:
        db_session: Optional SQLAlchemy session to use for database operations
    """
    if not NEW_TRIMS:
        return
    
    for trim_data in NEW_TRIMS:
        brand_name = trim_data.get('brand')
        model = trim_data.get('model')
        trim = trim_data.get('trim')
        
        # Here you could save to a new TrimMapping table or update Brand metadata
        # For now, just log that we found new trims
        logger.info(f"✅ New trim mapping discovered: {brand_name} {model} - {trim}")
    
    # Clear the list after processing
    NEW_TRIMS.clear()

def find_known_trim(brand_name, modification_text, db_session=None):
    """
    Check if modification text contains a known trim for the brand.
    Looks up trims from the database instead of hardcoded list.
    
    Args:
        brand_name (str): The brand name
        modification_text (str): The modification text to check for trims
        db_session: Optional SQLAlchemy session to use for queries
        
    Returns:
        str: Found trim or None
    """
    # Skip database check if no session is provided or modification is empty
    if not db_session or not modification_text:
        return None
        
    try:
        # Query potential trims for this brand from your database using provided session
        # Get cars of this brand that have trim values
        cars_with_trims = db_session.query(Car).join(Car.brand).filter(
            Brand.name == brand_name,
            Car.trim.isnot(None),
            Car.trim != ''
        ).all()
        
        # Extract unique trims
        possible_trims = set()
        for car in cars_with_trims:
            if car.trim and car.trim.strip():
                possible_trims.add(car.trim.strip())
        
        # Check if any known trim appears in the modification text
        for trim in possible_trims:
            if trim.lower() in modification_text.lower():
                return trim
                
    except Exception as e:
        logger.error(f"Error finding known trim for {brand_name}: {e}")
    
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
    carapi_key = os.getenv("CARAPI_API_KEY", "")
    if not carapi_key:
        logger.warning("⚠️ CARAPI_API_KEY not set in environment")
        return False
    
    cache_key = f"{brand.lower()}_{model.lower()}"
    
    # Check cache first
    if cache_key in API_RESULTS_CACHE.get('carapi', {}):
        cars = API_RESULTS_CACHE['carapi'][cache_key]
    else:
        try:
            url = f"https://carapi.app/api/v1/trims?make={brand.lower()}&model={model.lower()}"
            headers = {"Authorization": f"Bearer {carapi_key}"}
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

def parse_car_info(model_string, db_session=None):
    """
    Parse a car string in format [Brand] [Model] [Modification]
    and return normalized [Brand] [Model] [Modification] [Trim]
    
    Args:
        model_string (str): Car string in "[Brand] [Model] [Modification]" format
        db_session: Optional SQLAlchemy session to use for database operations
        
    Returns:
        dict: Dictionary with "brand", "model", "modification", and "trim" keys
    """
    parts = model_string.strip().split(' ')
    if len(parts) < 2:
        logger.warning(f"⚠️ Invalid car model string: {model_string}")
        return {
            "brand": parts[0] if parts else "",
            "model": "",
            "modification": "",
            "trim": "Standard"
        }
    
    # Try to identify the brand from the first word
    potential_brand = parts[0]
    brand_name = potential_brand
    brand_found = False
    
    # Check if the brand exists in our database (if session is provided)
    if db_session:
        try:
            # First check if it's a known synonym
            synonym = db_session.query(BrandSynonym).filter(BrandSynonym.name.ilike(potential_brand)).first()
            if synonym and synonym.brand:
                brand_name = synonym.brand.name
                brand_found = True
            
            if not brand_found:
                # Try to find the brand directly
                brand = db_session.query(Brand).filter(Brand.name.ilike(potential_brand)).first()
                if brand:
                    brand_name = brand.name
                    brand_found = True
        except Exception as e:
            logger.error(f"Error querying brand from database: {e}")
    
    if not brand_found:
        logger.warning(f"⚠️ Brand not validated in database: {potential_brand}")
    
    # Extract model - the second part is typically the model line
    model = parts[1]
    
    # Everything else is the modification text
    modification_text = ' '.join(parts[2:]) if len(parts) > 2 else ""
    
    # Now normalize using our brand-specific knowledge
    return normalize_car(brand_name, model, modification_text, db_session)

def normalize_car(brand, model, modification_text, db_session=None):
    """
    Normalize car data by extracting trim from modification text if possible
    
    Args:
        brand (str): Car brand
        model (str): Car model
        modification_text (str): Modification text which may include trim info
        db_session: Optional SQLAlchemy session to use for database operations
        
    Returns:
        dict: Dictionary with "brand", "model", "modification", and "trim" keys
    """
    # Find known trim in the modification text
    trim = find_known_trim(brand, modification_text, db_session)

    if not trim and modification_text:
        # If trim not found in our database, try to identify it
        words = modification_text.split()
        if len(words) <= 5:  # Only attempt for reasonably short phrases
            trim_candidate = modification_text

            # Verify with external APIs
            if check_trim_carquery(brand, model, trim_candidate) or check_trim_carapi(brand, model, trim_candidate):
                logger.info(f"✅ New trim identified: {trim_candidate}")
                NEW_TRIMS.append({
                    "brand": brand,
                    "model": model,
                    "modification": "",
                    "trim": trim_candidate
                })
                trim = trim_candidate
            else:
                logger.debug(f"Trim candidate not confirmed: {trim_candidate}")

    if trim:
        # Remove the trim from the modification text to avoid duplication
        mod_text = modification_text.lower().replace(trim.lower(), '', 1).strip().upper()
    else:
        mod_text = modification_text.upper()

    # Default modification to "Base" if it's empty after trim removal
    if not mod_text:
        mod_text = "Base"

    return {
        "brand": brand,
        "model": model,
        "modification": mod_text,
        "trim": trim or "Standard"
    }
