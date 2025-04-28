"""
Test engine extraction functionality
"""
import unittest
import sys
import os

# Add the parent directory to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the engine extraction function directly
from backend.utils.car_parser import extract_engine_info
# Update import path since we've moved the enum classes to models.py
from backend.models import EngineType, DriveType, TransmissionType

class TestEngineExtraction(unittest.TestCase):
    """Test engine information extraction from car text"""

    def test_displacement_extraction(self):
        """Test engine displacement extraction"""
        test_cases = [
            {"input": "Mercedes-Benz E-Class E 300 2.0T Avantgarde", "displacement": "2.0T"},
            {"input": "Toyota Camry 2.5L Prestige Safety", "displacement": "2.5L"},
            {"input": "Volkswagen Tiguan 2.0 TSI 4Motion R-Line", "displacement": "2.0 TSI"},
            {"input": "Kia EV6 77.4 kWh RWD GT-Line", "displacement": "77.4 kWh"},
        ]
        
        for test in test_cases:
            engine_data = extract_engine_info(test["input"])
            self.assertEqual(engine_data["displacement"], test["displacement"], 
                            f"Displacement extraction failed for: {test['input']}")
        
    def test_power_extraction(self):
        """Test engine power extraction"""
        test_cases = [
            {"input": "BMW X5 xDrive30d 249 hp M Sport", "power_hp": 249},
            {"input": "Toyota RAV4 Hybrid 222 HP E-Four Lounge", "power_hp": 222},
        ]
        
        for test in test_cases:
            engine_data = extract_engine_info(test["input"])
            self.assertEqual(engine_data["power_hp"], test["power_hp"],
                            f"Power extraction failed for: {test['input']}")
        
    def test_engine_type_detection(self):
        """Test engine type detection"""
        test_cases = [
            {"input": "Toyota RAV4 Hybrid 2.5L", "type": "hybrid"},
            {"input": "Audi A6 45 TFSI quattro Sport", "type": "gasoline"},
            {"input": "BMW X5 xDrive30d M Sport", "type": "diesel"},
            {"input": "Tesla Model Y Long Range AWD 77.4 kWh", "type": "electric"},
        ]
        
        for test in test_cases:
            engine_data = extract_engine_info(test["input"])
            self.assertEqual(engine_data["type"], test["type"],
                            f"Engine type detection failed for: {test['input']}")
        
    def test_drive_type_detection(self):
        """Test drive type detection"""
        test_cases = [
            {"input": "Audi A6 45 TFSI quattro Sport", "drive": "quattro"},
            {"input": "BMW X5 xDrive30d M Sport", "drive": "xdrive"},
            {"input": "Toyota RAV4 Hybrid AWD", "drive": "all_wheel_drive"},
            {"input": "Kia EV6 77.4 kWh RWD GT-Line", "drive": "rear_wheel_drive"},
            {"input": "Toyota RAV4 Hybrid E-Four", "drive": "e_four"},
        ]
        
        for test in test_cases:
            engine_data = extract_engine_info(test["input"])
            self.assertEqual(engine_data["drive"], test["drive"],
                            f"Drive type detection failed for: {test['input']}")
        
    def test_transmission_detection(self):
        """Test transmission detection"""
        test_cases = [
            {"input": "Volkswagen Golf 1.4 TSI DSG", "transmission": "dsg"},
            {"input": "Toyota Camry 2.5L CVT", "transmission": "cvt"},
            {"input": "Porsche 911 3.0T PDK", "transmission": "pdk"},
            {"input": "Hyundai Sonata 2.5 Smartstream DCT Style", "transmission": "dct"},
            {"input": "Toyota Corolla 1.6 МКПП", "transmission": "manual"},
            {"input": "Kia K5 2.5 АКПП", "transmission": "automatic"},
        ]
        
        for test in test_cases:
            engine_data = extract_engine_info(test["input"])
            self.assertEqual(engine_data["transmission"], test["transmission"],
                            f"Transmission detection failed for: {test['input']}")


if __name__ == "__main__":
    unittest.main()
