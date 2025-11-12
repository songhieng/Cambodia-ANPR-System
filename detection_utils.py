"""
Detection utilities for vehicle and license plate detection.
Contains common functions used across different detection scripts.
"""

import os
import cv2
import numpy as np
import datetime
from typing import Dict, List, Tuple, Optional, Any
import logging
from ultralytics import YOLO

from config import Config
from firebase_utils import FirebaseManager
from util import get_car, read_license_plate

logger = logging.getLogger(__name__)


class VehicleDetector:
    """Handles vehicle and license plate detection operations."""
    
    def __init__(
        self,
        coco_model_path: str,
        license_plate_model_path: str,
        car_type_model_path: Optional[str] = None,
        car_color_model_path: Optional[str] = None
    ):
        """
        Initialize the vehicle detector with YOLO models.
        
        Args:
            coco_model_path: Path to COCO YOLO model.
            license_plate_model_path: Path to license plate detection model.
            car_type_model_path: Optional path to car type classification model.
            car_color_model_path: Optional path to car color classification model.
        """
        try:
            self.coco_model = YOLO(coco_model_path)
            self.license_plate_detector = YOLO(license_plate_model_path)
            logger.info("Vehicle detection models loaded successfully")
            
            self.car_type_model = None
            if car_type_model_path:
                self.car_type_model = YOLO(car_type_model_path)
                logger.info("Car type model loaded successfully")
            
            self.car_color_model = None
            if car_color_model_path:
                self.car_color_model = YOLO(car_color_model_path)
                logger.info("Car color model loaded successfully")
                
        except Exception as e:
            logger.error(f"Failed to load detection models: {e}")
            raise
    
    def detect_vehicles(
        self,
        frame: np.ndarray,
        vehicle_classes: List[int]
    ) -> List[List[float]]:
        """
        Detect vehicles in a frame.
        
        Args:
            frame: Input video frame.
            vehicle_classes: List of COCO class IDs to detect.
            
        Returns:
            List of detections with bounding boxes and metadata.
        """
        try:
            detections = self.coco_model(frame)[0]
            vehicle_detections = []
            
            for detection in detections.boxes.data.tolist():
                x1, y1, x2, y2, score, class_id = detection
                if int(class_id) in vehicle_classes:
                    vehicle_detections.append([x1, y1, x2, y2, score, class_id])
            
            return vehicle_detections
        except Exception as e:
            logger.error(f"Error detecting vehicles: {e}")
            return []
    
    def detect_license_plates(
        self,
        frame: np.ndarray
    ) -> List[List[float]]:
        """
        Detect license plates in a frame.
        
        Args:
            frame: Input video frame.
            
        Returns:
            List of license plate detections.
        """
        try:
            license_plates = self.license_plate_detector(frame)[0]
            return license_plates.boxes.data.tolist()
        except Exception as e:
            logger.error(f"Error detecting license plates: {e}")
            return []
    
    def process_license_plate(
        self,
        frame: np.ndarray,
        license_plate: List[float]
    ) -> Tuple[Optional[str], Optional[float], Optional[np.ndarray]]:
        """
        Process a detected license plate to extract text.
        
        Args:
            frame: Input video frame.
            license_plate: License plate detection coordinates.
            
        Returns:
            Tuple of (license_text, confidence_score, processed_image).
        """
        try:
            x1, y1, x2, y2, score, class_id = license_plate
            
            license_plate_crop = frame[int(y1):int(y2), int(x1):int(x2), :]
            license_plate_crop_gray = cv2.cvtColor(
                license_plate_crop,
                cv2.COLOR_BGR2GRAY
            )
            _, license_plate_crop_thresh = cv2.threshold(
                license_plate_crop_gray,
                64,
                255,
                cv2.THRESH_BINARY_INV
            )
            
            license_plate_text, text_score = read_license_plate(
                license_plate_crop_thresh
            )
            
            return license_plate_text, text_score, license_plate_crop
        except Exception as e:
            logger.error(f"Error processing license plate: {e}")
            return None, None, None
    
    def classify_vehicle_type(
        self,
        car_image: np.ndarray
    ) -> Tuple[Optional[str], Optional[float]]:
        """
        Classify the type of vehicle.
        
        Args:
            car_image: Cropped image of the vehicle.
            
        Returns:
            Tuple of (vehicle_type, confidence).
        """
        if self.car_type_model is None:
            return None, None
        
        try:
            results = self.car_type_model(car_image)
            top_prediction_index = results[0].probs.top5[0]
            top_prediction_prob = results[0].probs.top5conf[0].item()
            
            car_type = Config.VEHICLE_TYPE_MAP.get(
                top_prediction_index,
                'Unknown'
            )
            return car_type, top_prediction_prob
        except Exception as e:
            logger.error(f"Error classifying vehicle type: {e}")
            return None, None
    
    def classify_vehicle_color(
        self,
        car_image: np.ndarray
    ) -> Tuple[Optional[str], Optional[float]]:
        """
        Classify the color of vehicle.
        
        Args:
            car_image: Cropped image of the vehicle.
            
        Returns:
            Tuple of (vehicle_color, confidence).
        """
        if self.car_color_model is None:
            return None, None
        
        try:
            results = self.car_color_model(car_image)
            top_prediction_index = results[0].probs.top5[0]
            top_prediction_prob = results[0].probs.top5conf[0].item()
            
            car_color = Config.VEHICLE_COLOR_MAP.get(
                top_prediction_index,
                'Unknown'
            )
            return car_color, top_prediction_prob
        except Exception as e:
            logger.error(f"Error classifying vehicle color: {e}")
            return None, None


def save_detection_images(
    car_image: np.ndarray,
    plate_image: np.ndarray,
    license_plate_text: str,
    car_type: Optional[str] = None,
    car_color: Optional[str] = None,
    firebase_manager: Optional[FirebaseManager] = None
) -> Tuple[str, str]:
    """
    Save detected car and license plate images locally and optionally to Firebase.
    
    Args:
        car_image: Cropped car image.
        plate_image: Cropped license plate image.
        license_plate_text: Detected license plate text.
        car_type: Optional vehicle type.
        car_color: Optional vehicle color.
        firebase_manager: Optional Firebase manager for cloud upload.
        
    Returns:
        Tuple of (car_image_path, plate_image_path).
    """
    try:
        Config.ensure_directories()
        
        timestamp_str = datetime.datetime.utcnow().replace(
            microsecond=0
        ).isoformat()
        timestamp_int = int(datetime.datetime.utcnow().timestamp() * 1000)
        
        # Build filenames
        car_filename = f"car_{license_plate_text}"
        plate_filename = f"plate_{license_plate_text}"
        
        if car_color and car_type:
            car_filename += f"_{car_color}_{car_type}"
        
        car_filename += f"_{timestamp_str}_{timestamp_int}.jpg"
        plate_filename += f"_{timestamp_str}_{timestamp_int}.jpg"
        
        # Save locally
        car_image_path = os.path.join(Config.CAR_OUTPUT_DIR, car_filename)
        plate_image_path = os.path.join(Config.PLATE_OUTPUT_DIR, plate_filename)
        
        cv2.imwrite(car_image_path, car_image)
        cv2.imwrite(plate_image_path, plate_image)
        
        # Upload to Firebase if manager is provided
        if firebase_manager:
            firebase_manager.upload_to_storage(
                car_image_path,
                f"detected_cars/{car_filename}"
            )
            firebase_manager.upload_to_storage(
                plate_image_path,
                f"detected_plates/{plate_filename}"
            )
        
        return car_image_path, plate_image_path
    except Exception as e:
        logger.error(f"Error saving detection images: {e}")
        raise


def check_flagged_plate(
    license_plate_text: str,
    flagged_plates: List[str]
) -> bool:
    """
    Check if a license plate is in the flagged list.
    
    Args:
        license_plate_text: License plate text to check.
        flagged_plates: List of flagged license plates.
        
    Returns:
        True if the plate is flagged, False otherwise.
    """
    return license_plate_text in flagged_plates
