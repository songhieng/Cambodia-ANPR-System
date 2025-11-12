"""
Vehicle type classification utility.
Simple script to test vehicle type/make detection on single images.
"""

from typing import Optional
import logging
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def classify_vehicle_make(image_path: str, model_path: str = "make.pt") -> Optional[str]:
    """
    Classify the make of a vehicle from an image.
    
    Args:
        image_path: Path to the vehicle image.
        model_path: Path to the YOLO model for vehicle make classification.
        
    Returns:
        Vehicle make classification result or None if error occurs.
    """
    try:
        model = YOLO(model_path)
        result = model(image_path)
        logger.info(f"Vehicle make classification result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error classifying vehicle make: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    test_image = '2.jpg'
    result = classify_vehicle_make(test_image)
    if result:
        print(f"Classification complete: {result}")
