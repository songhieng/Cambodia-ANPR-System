"""
Configuration module for the Cambodia ANPR System.
Handles environment variables and Firebase configuration.
"""

import os
from typing import Dict, Any


class Config:
    """Configuration class for application settings."""
    
    # Firebase Configuration
    FIREBASE_CREDENTIALS_PATH: str = os.environ.get(
        'FIREBASE_CREDENTIALS_PATH',
        'firebase-credentials.json'
    )
    FIREBASE_DATABASE_URL: str = os.environ.get(
        'FIREBASE_DATABASE_URL',
        ''
    )
    FIREBASE_STORAGE_BUCKET: str = os.environ.get(
        'FIREBASE_STORAGE_BUCKET',
        ''
    )
    
    # Model Paths
    YOLO_MODEL_PATH: str = 'yolov8n.pt'
    LICENSE_PLATE_MODEL_PATH: str = './models/run46.pt'
    CAR_TYPE_MODEL_PATH: str = 'car.pt'
    CAR_COLOR_MODEL_PATH: str = 'color.pt'
    CAR_MAKE_MODEL_PATH: str = 'make.pt'
    
    # Detection Settings
    FRAME_SKIP: int = 40
    VEHICLE_CLASS_IDS: list = [2, 3, 4, 5, 6, 7]  # COCO dataset vehicle classes
    
    # Output Directories
    CAR_OUTPUT_DIR: str = 'detected_cars'
    PLATE_OUTPUT_DIR: str = 'detected_plates'
    DATA_OUTPUT_DIR: str = 'DATA'
    
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
    
    # COCO Class to Vehicle Type Mapping
    COCO_CLASS_TO_VEHICLE: Dict[int, str] = {
        2: 'car',
        3: 'motorcycle',
        4: 'airplane',
        5: 'bus',
        6: 'train',
        7: 'truck'
    }
    
    @staticmethod
    def ensure_directories() -> None:
        """Ensure all required output directories exist."""
        directories = [
            Config.CAR_OUTPUT_DIR,
            Config.PLATE_OUTPUT_DIR,
            Config.DATA_OUTPUT_DIR
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)


def get_firebase_config() -> Dict[str, Any]:
    """
    Get Firebase configuration.
    
    Returns:
        Dictionary with Firebase configuration.
    
    Raises:
        ValueError: If required configuration is missing.
    """
    if not Config.FIREBASE_DATABASE_URL or not Config.FIREBASE_STORAGE_BUCKET:
        raise ValueError(
            "Firebase configuration is incomplete. Please set "
            "FIREBASE_DATABASE_URL and FIREBASE_STORAGE_BUCKET environment variables."
        )
    
    return {
        'databaseURL': Config.FIREBASE_DATABASE_URL,
        'storageBucket': Config.FIREBASE_STORAGE_BUCKET
    }
