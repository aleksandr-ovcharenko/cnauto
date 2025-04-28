from enum import Enum
from datetime import datetime


class EngineType(Enum):
    """Engine types"""
    GASOLINE = "gasoline"
    DIESEL = "diesel"
    HYBRID = "hybrid"
    PLUGIN_HYBRID = "plugin_hybrid"
    ELECTRIC = "electric"
    LPG = "lpg"
    CNG = "cng"
    HYDROGEN = "hydrogen"


class DriveType(Enum):
    """Drive types"""
    FWD = "front_wheel_drive"
    RWD = "rear_wheel_drive"
    AWD = "all_wheel_drive"
    QUATTRO = "quattro"
    XDRIVE = "xdrive"
    E_FOUR = "e_four"


class TransmissionType(Enum):
    """Transmission types"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    CVT = "cvt"
    DCT = "dct"
    DSG = "dsg"
    PDK = "pdk"
    AMT = "amt"


class CarEngine:
    """Engine information stored with a car"""
    # Basic engine data
    displacement = None  # Объем двигателя или батареи (например, "1.6T" или "77.4 kWh")
    power_hp = None        # Мощность в лошадиных силах
    type = None         # Тип двигателя (EngineType)
    drive = None        # Тип привода (DriveType)
    transmission = None # Коробка передач
    
    # Original text and description
    engine_text = None  # Original parsed text
    description = None  # Generated or imported description
    
    created_at = None
    
    # Relationship
    car = None
    
    def generate_description(self):
        """Generate a human-readable engine description"""
        parts = []
        if self.displacement:
            parts.append(str(self.displacement))
        if self.power_hp:
            parts.append(f"{self.power_hp} л.с.")
        if self.drive:
            # Map drive type to Russian text
            drive_map = {
                "front_wheel_drive": "передний привод", 
                "rear_wheel_drive": "задний привод",
                "all_wheel_drive": "полный привод",
                "quattro": "quattro",
                "xdrive": "xDrive",
                "e_four": "E-Four"
            }
            drive_text = drive_map.get(self.drive, self.drive)
            parts.append(drive_text)
        if self.transmission:
            parts.append(f"КПП: {self.transmission}")
        
        return ", ".join(parts) if parts else (self.description or "-")
    
    def __repr__(self):
        return self.generate_description()
