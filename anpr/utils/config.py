"""
Configuration Module

Centralized configuration for the Cambodia ANPR System.
Manages model paths, detection settings, and Firebase credentials.
"""

import os
from typing import Dict, Any
from pathlib import Path


class Config:
    """Application configuration and settings."""
    
    # Base paths
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    MODEL_DIR = BASE_DIR / "anpr" / "models" / "weights"
    OUTPUT_DIR = BASE_DIR / "outputs"
    LOG_DIR = BASE_DIR / "logs"
    CONFIG_DIR = BASE_DIR / "config"
    
    # Firebase Configuration
    FIREBASE_CREDENTIALS_PATH: str = os.environ.get(
        'FIREBASE_CREDENTIALS_PATH',
        str(CONFIG_DIR / 'firebase-credentials.json')
    )
    FIREBASE_DATABASE_URL: str = os.environ.get(
        'FIREBASE_DATABASE_URL',
        ''
    )
    FIREBASE_STORAGE_BUCKET: str = os.environ.get(
        'FIREBASE_STORAGE_BUCKET',
        ''
    )
    
    # Model Paths (relative to MODEL_DIR)
    YOLO_MODEL_PATH: str = str(MODEL_DIR / 'yolov8n.pt')
    LICENSE_PLATE_MODEL_PATH: str = str(MODEL_DIR / 'run46.pt')
    CAR_TYPE_MODEL_PATH: str = str(MODEL_DIR / 'car.pt')
    CAR_COLOR_MODEL_PATH: str = str(MODEL_DIR / 'color.pt')
    CAR_MAKE_MODEL_PATH: str = str(MODEL_DIR / 'make.pt')
    
    # Detection Settings
    FRAME_SKIP: int = int(os.environ.get('FRAME_SKIP', '40'))
    VEHICLE_CLASS_IDS: list = [2, 3, 5, 7]  # car, motorcycle, bus, truck
    
    # Output Directories
    CAR_OUTPUT_DIR: str = str(OUTPUT_DIR / 'detected_cars')
    PLATE_OUTPUT_DIR: str = str(OUTPUT_DIR / 'detected_plates')
    DEMO_OUTPUT_DIR: str = str(OUTPUT_DIR / 'demo_results')
    FLAGGED_OUTPUT_DIR: str = str(OUTPUT_DIR / 'flagged')
    
    # Vehicle Type Mapping
    VEHICLE_TYPE_MAP: Dict[int, str] = {
        0: 'Convertible',
        1: 'Coupe',
        2: 'Hatchback',
        3: 'Pickup',
        4: 'SUV',
        5: 'Sedan'
    }
    
    # Vehicle Color Mapping
    VEHICLE_COLOR_MAP: Dict[int, str] = {
        0: 'beige',
        1: 'black',
        2: 'blue',
        3: 'brown',
        4: 'gold',
        5: 'green',
        6: 'grey',
        7: 'orange',
        8: 'pink',
        9: 'purple',
        10: 'red',
        11: 'silver',
        12: 'tan',
        13: 'white',
        14: 'yellow'
    }
    
    # COCO Class ID to Vehicle Type Mapping
    COCO_CLASS_TO_VEHICLE: Dict[int, str] = {
        2: 'car',
        3: 'motorcycle',
        5: 'bus',
        7: 'truck'
    }
    
    @staticmethod
    def ensure_directories() -> None:
        """Create all required output directories if they don't exist."""
        directories = [
            Config.OUTPUT_DIR,
            Config.CAR_OUTPUT_DIR,
            Config.PLATE_OUTPUT_DIR,
            Config.DEMO_OUTPUT_DIR,
            Config.FLAGGED_OUTPUT_DIR,
            Config.LOG_DIR,
            Config.CONFIG_DIR
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)


def get_firebase_config() -> Dict[str, Any]:
    """
    Retrieve Firebase configuration from environment.
    
    Returns:
        Dictionary containing Firebase configuration parameters.
    """
    return {
        'credentials_path': Config.FIREBASE_CREDENTIALS_PATH,
        'database_url': Config.FIREBASE_DATABASE_URL,
        'storage_bucket': Config.FIREBASE_STORAGE_BUCKET
    }
