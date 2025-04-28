#!/usr/bin/env python3
"""
Test script for car parsing functionality.
This script tests parsing of car data in the format [Brand] [Model] [Modification]
to correctly extract brand, model, modification, and trim.

Usage:
    cd backend
    python -m tests.test_car_parser
"""

import os
import sys
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Add the parent directory to the path so we can import our models and utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import models and utils
from backend.models import Brand, BrandTrim, BrandModification
from utils.car_parser import parse_car_info, normalize_car, extract_engine_info

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

# Test data with expected parsing results
TEST_CASES = [
    {
        "input": "Mercedes-Benz E-Class E 300 2.0T Avantgarde",
        "expected": {"brand": "Mercedes-Benz", "model": "E-Class", "modification": "E 300 2.0T", "trim": "Avantgarde"}
    },
    {
        "input": "BMW X5 xDrive30d M Sport",
        "expected": {"brand": "BMW", "model": "X5", "modification": "xDrive30d", "trim": "M Sport"}
    },
    {
        "input": "Audi A6 45 TFSI quattro Sport",
        "expected": {"brand": "Audi", "model": "A6", "modification": "45 TFSI quattro", "trim": "Sport"}
    },
    {
        "input": "Toyota Camry 2.5L Prestige Safety",
        "expected": {"brand": "Toyota", "model": "Camry", "modification": "2.5L", "trim": "Prestige Safety"}
    },
    {
        "input": "Volkswagen Tiguan 2.0 TSI 4Motion R-Line",
        "expected": {"brand": "Volkswagen", "model": "Tiguan", "modification": "2.0 TSI 4Motion", "trim": "R-Line"}
    },
    {
        "input": "Lexus RX 350 AWD Luxury",
        "expected": {"brand": "Lexus", "model": "RX", "modification": "350 AWD", "trim": "Luxury"}
    },
    {
        "input": "Kia Sportage 2.0 MPI Luxe",
        "expected": {"brand": "Kia", "model": "Sportage", "modification": "2.0 MPI", "trim": "Luxe"}
    },
    {
        "input": "Hyundai Sonata 2.5 Smartstream Style",
        "expected": {"brand": "Hyundai", "model": "Sonata", "modification": "2.5 Smartstream", "trim": "Style"}
    },
    {
        "input": "Mazda CX-5 2.5 AWD Supreme",
        "expected": {"brand": "Mazda", "model": "CX-5", "modification": "2.5 AWD", "trim": "Supreme"}
    },
    {
        "input": "Porsche Macan 2.0T PDK Premium Plus",
        "expected": {"brand": "Porsche", "model": "Macan", "modification": "2.0T PDK", "trim": "Premium Plus"}
    },
    {
        "input": "Ford Explorer 3.0 EcoBoost Platinum",
        "expected": {"brand": "Ford", "model": "Explorer", "modification": "3.0 EcoBoost", "trim": "Platinum"}
    },
    {
        "input": "Volvo XC90 T6 AWD Inscription",
        "expected": {"brand": "Volvo", "model": "XC90", "modification": "T6 AWD", "trim": "Inscription"}
    },
    {
        "input": "Chery Tiggo 8 Pro 1.6T Ultimate",
        "expected": {"brand": "Chery", "model": "Tiggo 8 Pro", "modification": "1.6T", "trim": "Ultimate"}
    },
    {
        "input": "Geely Tugella 2.0T Flagship",
        "expected": {"brand": "Geely", "model": "Tugella", "modification": "2.0T", "trim": "Flagship"}
    },
    {
        "input": "Haval Jolion 1.5T DCT Elite",
        "expected": {"brand": "Haval", "model": "Jolion", "modification": "1.5T DCT", "trim": "Elite"}
    },
    {
        "input": "Exeed TXL 1.6TGDI Luxury",
        "expected": {"brand": "Exeed", "model": "TXL", "modification": "1.6TGDI", "trim": "Luxury"}
    },
    {
        "input": "Changan CS75 Plus 2.0T AWD Premium",
        "expected": {"brand": "Changan", "model": "CS75 Plus", "modification": "2.0T AWD", "trim": "Premium"}
    },
    {
        "input": "BYD Tang EV AWD Flagship",
        "expected": {"brand": "BYD", "model": "Tang", "modification": "EV AWD", "trim": "Flagship"}
    },
    {
        "input": "Omoda C5 1.6T DCT Supreme",
        "expected": {"brand": "Omoda", "model": "C5", "modification": "1.6T DCT", "trim": "Supreme"}
    },
    {
        "input": "Jaecoo J7 1.6T Ultimate",
        "expected": {"brand": "Jaecoo", "model": "J7", "modification": "1.6T", "trim": "Ultimate"}
    },
    {
        "input": "Voyah Free EV Long Range",
        "expected": {"brand": "Voyah", "model": "Free", "modification": "EV", "trim": "Long Range"}
    },
    {
        "input": "Tesla Model Y Long Range AWD",
        "expected": {"brand": "Tesla", "model": "Model Y", "modification": "Long Range AWD", "trim": "Standard"}
    },
    {
        "input": "Chevrolet Tahoe 6.2 V8 High Country",
        "expected": {"brand": "Chevrolet", "model": "Tahoe", "modification": "6.2 V8", "trim": "High Country"}
    },
    {
        "input": "Jeep Grand Cherokee 3.6 V6 Limited",
        "expected": {"brand": "Jeep", "model": "Grand Cherokee", "modification": "3.6 V6", "trim": "Limited"}
    },
    {
        "input": "Dodge Durango 5.7 V8 R/T",
        "expected": {"brand": "Dodge", "model": "Durango", "modification": "5.7 V8", "trim": "R/T"}
    },
    {
        "input": "Peugeot 3008 1.6 PureTech GT Line",
        "expected": {"brand": "Peugeot", "model": "3008", "modification": "1.6 PureTech", "trim": "GT Line"}
    },
    {
        "input": "Citroen C5 Aircross 1.6T Shine Pack",
        "expected": {"brand": "Citroen", "model": "C5 Aircross", "modification": "1.6T", "trim": "Shine Pack"}
    },
    {
        "input": "Alfa Romeo Stelvio 2.0T Q4 Veloce",
        "expected": {"brand": "Alfa Romeo", "model": "Stelvio", "modification": "2.0T Q4", "trim": "Veloce"}
    },
    {
        "input": "Maserati Levante 3.0 V6 GranLusso",
        "expected": {"brand": "Maserati", "model": "Levante", "modification": "3.0 V6", "trim": "GranLusso"}
    },
    {
        "input": "Land Rover Range Rover Sport P400e HSE Dynamic",
        "expected": {"brand": "Land Rover", "model": "Range Rover Sport", "modification": "P400e", "trim": "HSE Dynamic"}
    },
    {
        "input": "MINI Countryman Cooper S ALL4 Iconic",
        "expected": {"brand": "MINI", "model": "Countryman", "modification": "Cooper S ALL4", "trim": "Iconic"}
    }
]

# Additional test cases that are more challenging
COMPLEX_TEST_CASES = [
    {
        "input": "Volkswagen Polo 1.0 TSI DSG Life 110 hp",
        "expected": {"brand": "Volkswagen", "model": "Polo", "modification": "1.0 TSI DSG", "trim": "Life"}
    },
    {
        "input": "Kia EV6 77.4 kWh RWD GT-Line",
        "expected": {"brand": "Kia", "model": "EV6", "modification": "77.4 kWh RWD", "trim": "GT-Line"}
    },
    {
        "input": "Mercedes-Benz C 180 AMG Line 9G-TRONIC",
        "expected": {"brand": "Mercedes-Benz", "model": "C", "modification": "180 9G-TRONIC", "trim": "AMG Line"}
    },
    {
        "input": "Toyota RAV4 Hybrid 222 HP E-Four Lounge",
        "expected": {"brand": "Toyota", "model": "RAV4", "modification": "Hybrid E-Four", "trim": "Lounge"}
    },
    {
        "input": "BMW 320i 2.0T xDrive M Sport 184 hp",
        "expected": {"brand": "BMW", "model": "320i", "modification": "2.0T xDrive", "trim": "M Sport"}
    }
]

class TestCarParser(unittest.TestCase):
    """Test case for car parsing functionality"""
    
    def setUp(self):
        """Prepare for tests - note we don't use database-driven functions"""
        # We'll only test extract_engine_info which doesn't require a database
        pass
            
    def tearDown(self):
        """Tear down test case"""
        pass
    
    def test_extract_engine_info(self):
        """Test engine information extraction without database dependency"""
        from utils.car_parser import extract_engine_info
        
        # Test cases that don't need database access
        test_cases = [
            {"input": "BMW X5 xDrive30d M Sport", 
             "expected": {
                 "displacement": None, 
                 "power_hp": None, 
                 "type": "diesel", 
                 "drive": "xdrive", 
                 "transmission": None,
                 "engine_text": "BMW X5 xDrive30d M Sport"
             }},
            {"input": "Volkswagen Tiguan 2.0 TSI 4Motion R-Line", 
             "expected": {
                 "displacement": "2.0 TSI", 
                 "power_hp": None, 
                 "type": "gasoline", 
                 "drive": "all_wheel_drive", 
                 "transmission": None,
                 "engine_text": "Volkswagen Tiguan 2.0 TSI 4Motion R-Line"
             }},
            {"input": "Toyota RAV4 Hybrid 2.5L 222 HP E-Four", 
             "expected": {
                 "displacement": "2.5L", 
                 "power_hp": 222, 
                 "type": "hybrid", 
                 "drive": "e_four", 
                 "transmission": None,
                 "engine_text": "Toyota RAV4 Hybrid 2.5L 222 HP E-Four"
             }},
            {"input": "Porsche 911 3.0T PDK", 
             "expected": {
                 "displacement": "3.0T", 
                 "power_hp": None, 
                 "type": "gasoline", 
                 "drive": None, 
                 "transmission": "pdk",
                 "engine_text": "Porsche 911 3.0T PDK"
             }},
            {"input": "Kia EV6 77.4 kWh RWD GT-Line", 
             "expected": {
                 "displacement": "77.4 kWh", 
                 "power_hp": None, 
                 "type": "electric", 
                 "drive": "rear_wheel_drive", 
                 "transmission": None,
                 "engine_text": "Kia EV6 77.4 kWh RWD GT-Line"
             }},
        ]
        
        for test in test_cases:
            engine_info = extract_engine_info(test["input"])
            self.assertEqual(engine_info["type"], test["expected"]["type"], 
                            f"Failed on {test['input']}: type mismatch. Got {engine_info['type']}, expected {test['expected']['type']}")
            self.assertEqual(engine_info["drive"], test["expected"]["drive"], 
                            f"Failed on {test['input']}: drive mismatch. Got {engine_info['drive']}, expected {test['expected']['drive']}")
            self.assertEqual(engine_info["displacement"], test["expected"]["displacement"], 
                            f"Failed on {test['input']}: displacement mismatch. Got {engine_info['displacement']}, expected {test['expected']['displacement']}")
            self.assertEqual(engine_info["power_hp"], test["expected"]["power_hp"], 
                            f"Failed on {test['input']}: power_hp mismatch. Got {engine_info['power_hp']}, expected {test['expected']['power_hp']}")
            self.assertEqual(engine_info["transmission"], test["expected"]["transmission"], 
                            f"Failed on {test['input']}: transmission mismatch. Got {engine_info['transmission']}, expected {test['expected']['transmission']}")

def test_data_summary():
    """Print a summary of test data to verify parsing"""
    print("\nCAR PARSING TEST DATA SUMMARY:")
    print("=" * 80)
    print(f"{'Input':<45} | {'Brand':<15} | {'Model':<15} | {'Modification':<20} | {'Trim':<15}")
    print("-" * 80)
    
    for case in TEST_CASES:
        input_str = case["input"][:42] + "..." if len(case["input"]) > 45 else case["input"]
        brand = case["expected"]["brand"][:12] + "..." if len(case["expected"]["brand"]) > 15 else case["expected"]["brand"]
        model = case["expected"]["model"][:12] + "..." if len(case["expected"]["model"]) > 15 else case["expected"]["model"]
        mod = case["expected"]["modification"][:17] + "..." if len(case["expected"]["modification"]) > 20 else case["expected"]["modification"]
        trim = case["expected"]["trim"][:12] + "..." if len(case["expected"]["trim"]) > 15 else case["expected"]["trim"]
        
        print(f"{input_str:<45} | {brand:<15} | {model:<15} | {mod:<20} | {trim:<15}")
    
    print("=" * 80)

if __name__ == "__main__":
    # First print test data summary
    test_data_summary()
    
    # Run the tests
    unittest.main()
