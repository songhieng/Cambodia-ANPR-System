"""
ANPR CLI Application

Command-line interface for processing video files.
Integrates with Firebase for data storage and flagged vehicle detection.

Usage:
    python -m apps.cli --video path/to/video.mp4
    python -m apps.cli --video f1.mp4 --no-firebase
"""

import argparse
import os
import datetime
from typing import Dict, Any
from pathlib import Path
import cv2
import numpy as np
from dotenv import load_dotenv

from anpr.tracking.sort import Sort
from anpr.utils.config import Config
from anpr.utils.logger import get_logger
from anpr.integrations.firebase import get_firebase_manager
from anpr.core.detector import ANPRDetector
from anpr.core.ocr import OCREngine

logger = get_logger(__name__)
load_dotenv()


def process_flagged_vehicles(
    detected_plates: Dict[str, Any],
    database_data: list,
    firebase_manager
) -> None:
    """
    Identify and flag vehicles whose plates match the watchlist database.
    
    Args:
        detected_plates: Dictionary mapping UIDs to detected vehicle details.
        database_data: List of vehicle records from watchlist database.
        firebase_manager: Firebase manager instance for database operations.
    """
    try:
        if not database_data:
            logger.info("No database records to compare against")
            return
            
        # Build watchlist of plates
        watchlist_plates = {
            entry.get('License_Plate')
            for entry in database_data
            if entry.get('License_Plate')
        }
        
        if not watchlist_plates:
            logger.warning("Watchlist database contains no valid license plates")
            return
        
        # Find matches
        flagged_vehicles = {}
        flagged_details = {}
        
        for uid, details in detected_plates.items():
            license_plate = details.get('license_plate')
            if license_plate in watchlist_plates:
                flagged_vehicles[uid] = details
                
                # Find full details from database
                for entry in database_data:
                    if entry.get('License_Plate') == license_plate:
                        flagged_details[license_plate] = entry
                        break
        
        # Upload flagged data
        if flagged_vehicles:
            firebase_manager.set_data('flagged', flagged_vehicles)
            firebase_manager.set_data('flagged_details', flagged_details)
            logger.warning(f"ALERT: {len(flagged_vehicles)} flagged vehicles detected!")
            for uid, details in flagged_vehicles.items():
                logger.warning(f"  - {details.get('license_plate')}")
        else:
            logger.info("No flagged vehicles detected")
            
    except Exception as e:
        logger.error(f"Error processing flagged vehicles: {e}", exc_info=True)


def main(video_path: str, use_firebase: bool = True):
    """
    Main execution function for ANPR video processing.
    
    Args:
        video_path: Path to video file to process.
        use_firebase: Whether to use Firebase integration.
    """
    try:
        logger.info("Starting ANPR Detection System...")
        
        # Initialize Firebase if requested
        firebase_manager = None
        if use_firebase:
            try:
                firebase_manager = get_firebase_manager()
                credentials_path = Config.FIREBASE_CREDENTIALS_PATH
                database_url = Config.FIREBASE_DATABASE_URL
                storage_bucket = Config.FIREBASE_STORAGE_BUCKET
                
                if os.path.exists(credentials_path):
                    firebase_manager.initialize(credentials_path, database_url, storage_bucket)
                    logger.info("Firebase initialized successfully")
                else:
                    logger.warning(f"Firebase credentials not found at {credentials_path}")
                    firebase_manager = None
            except Exception as e:
                logger.warning(f"Firebase initialization failed: {e}")
                firebase_manager = None
        
        # Ensure output directories exist
        Config.ensure_directories()
        
        # Initialize detector
        logger.info("Initializing ANPR detector...")
        detector = ANPRDetector(enable_classification=True)
        ocr_engine = OCREngine()
        
        # Initialize tracker
        mot_tracker = Sort()
        results = {}
        
        # Load video
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        logger.info(f"Processing video: {video_path} ({total_frames} frames)")
        
        frame_nmr = -1
        ret = True
        
        while ret:
            frame_nmr += 1
            ret, frame = cap.read()
            
            if ret and frame_nmr % Config.FRAME_SKIP == 0:
                logger.info(f"Processing frame {frame_nmr}/{total_frames}")
                results[frame_nmr] = {}
                
                # Detect vehicles
                detections = detector.detect_vehicles(frame)
                
                if detections:
                    logger.debug(f"Detected {len(detections)} vehicles in frame {frame_nmr}")
                
                # Track vehicles
                tracking_data = np.array([[d[0], d[1], d[2], d[3], d[4]] for d in detections])
                track_ids = mot_tracker.update(tracking_data) if len(tracking_data) > 0 else np.array([])
                
                # Detect license plates
                license_plates = detector.detect_license_plates(frame)
                
                if license_plates:
                    logger.debug(f"Detected {len(license_plates)} license plates")
                
                for license_plate in license_plates:
                    x1, y1, x2, y2, score, class_id = license_plate
                    
                    # Assign license plate to detected car
                    xcar1, ycar1, xcar2, ycar2, car_id = ocr_engine.get_vehicle_for_plate(
                        license_plate,
                        track_ids
                    )
                    
                    if car_id != -1:
                        logger.debug(f"Matched plate to Car ID: {car_id}")
                        
                        # Process and read license plate
                        license_plate_text, text_score, plate_image = detector.process_license_plate(
                            frame,
                            license_plate
                        )
                        
                        if license_plate_text is not None:
                            logger.info(f"Detected: {license_plate_text} (conf: {text_score:.2f})")
                            
                            # Extract car image
                            car_image = frame[int(ycar1):int(ycar2), int(xcar1):int(xcar2), :]
                            
                            # Classify vehicle
                            car_type, type_conf = detector.classify_vehicle_type(car_image)
                            car_color, color_conf = detector.classify_vehicle_color(car_image)
                            
                            # Save detection images
                            from anpr.core.detector import save_detection_images
                            try:
                                car_path, plate_path = save_detection_images(
                                    car_image,
                                    plate_image,
                                    license_plate_text,
                                    car_type,
                                    car_color,
                                    firebase_manager=firebase_manager
                                )
                                
                                # Upload to Firebase database
                                if firebase_manager:
                                    firebase_manager.push_data('users_detected', {
                                        'license_plate': license_plate_text,
                                        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        'car_image_path': car_path,
                                        'plate_image_path': plate_path,
                                        'confidence': float(text_score),
                                        'type': car_type,
                                        'color': car_color
                                    })
                                
                                # Store in local results
                                results[frame_nmr][car_id] = {
                                    'car': {
                                        'bbox': [xcar1, ycar1, xcar2, ycar2],
                                        'type': car_type,
                                        'color': car_color
                                    },
                                    'license_plate': {
                                        'bbox': [x1, y1, x2, y2],
                                        'text': license_plate_text,
                                        'bbox_score': float(score),
                                        'text_score': float(text_score)
                                    }
                                }
                            except Exception as e:
                                logger.error(f"Error saving detection: {e}")
        
        cap.release()
        logger.info(f"Video processing completed. Processed {frame_nmr + 1} frames.")
        
        # Check for flagged vehicles
        if firebase_manager:
            logger.info("Checking for flagged vehicles...")
            try:
                detected_data = firebase_manager.get_data('users_detected')
                database_data = firebase_manager.get_data('users_database')
                
                if detected_data:
                    detected_plates = {
                        uid: details for uid, details in detected_data.items()
                    }
                    process_flagged_vehicles(detected_plates, database_data or [], firebase_manager)
                else:
                    logger.info("No detected plates to check")
                    
            except Exception as e:
                logger.error(f"Error checking flagged vehicles: {e}")
        
        logger.info("ANPR Detection System completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ANPR CLI Application")
    parser.add_argument(
        '--video',
        type=str,
        default='f1.mp4',
        help='Path to input video file'
    )
    parser.add_argument(
        '--no-firebase',
        action='store_true',
        help='Disable Firebase integration'
    )
    
    args = parser.parse_args()
    
    main(video_path=args.video, use_firebase=not args.no_firebase)
