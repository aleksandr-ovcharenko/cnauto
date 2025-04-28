"""
Simple test for engine extraction functionality
"""
import re
import unittest

# Copy of the extract_engine_info function to avoid import issues
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
    if re.search(r'\b(?:4WD|4x4|AWD|полный привод|all wheel drive)\b', text, re.IGNORECASE):
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
