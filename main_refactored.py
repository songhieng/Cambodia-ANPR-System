"""
Main script for vehicle and license plate detection system.
Processes video to detect vehicles, read license plates, and flag suspicious plates.
"""

import os
import logging
from typing import Dict, Any
import cv2
import numpy as np
from dotenv import load_dotenv

from sort.sort import Sort
from config import Config
from firebase_utils import get_firebase_manager
from detection_utils import VehicleDetector, save_detection_images, check_flagged_plate

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def process_flagged_vehicles(
    detected_plates: Dict[str, Any],
    database_plates: Dict[str, Any],
    firebase_manager
) -> None:
    """
    Compare detected plates with database and flag suspicious vehicles.
    
    Args:
        detected_plates: Dictionary of detected license plates.
        database_plates: Dictionary of plates from database.
        firebase_manager: Firebase manager instance.
    """
    try:
        flagged_data = {}
        
        for uid, details in detected_plates.items():
            license_plate = details.get('license_plate')
            if license_plate in database_plates.values():
                flagged_data[uid] = details
        
        if flagged_data:
            firebase_manager.set_data('flagged', flagged_data)
            logger.info(f"Flagged {len(flagged_data)} suspicious vehicles")
            
            flagged_details = {}
            for uid in flagged_data:
                license_plate = flagged_data[uid]['license_plate']
                for user_id, user_data in enumerate(database_plates):
                    if user_data.get('License_Plate') == license_plate:
                        flagged_details[user_id] = user_data
            
            if flagged_details:
                firebase_manager.set_data('flagged_details', flagged_details)
                logger.info("Flagged details uploaded to Firebase")
    except Exception as e:
        logger.error(f"Error processing flagged vehicles: {e}")


def main():
    """Main execution function."""
    try:
        # Initialize Firebase
        firebase_manager = get_firebase_manager()
        
        credentials_path = os.environ.get(
            'FIREBASE_CREDENTIALS_PATH',
            'anpr-5a023-firebase-adminsdk-mrrmo-d159fa0e4d.json'
        )
        database_url = os.environ.get(
            'FIREBASE_DATABASE_URL',
            'https://anpr-5a023-default-rtdb.asia-southeast1.firebasedatabase.app'
        )
        storage_bucket = os.environ.get(
            'FIREBASE_STORAGE_BUCKET',
            'anpr-5a023.appspot.com'
        )
        
        firebase_manager.initialize(
            credentials_path,
            database_url,
            storage_bucket
        )
        
        # Ensure output directories exist
        Config.ensure_directories()
        
        # Initialize vehicle detector
        detector = VehicleDetector(
            Config.YOLO_MODEL_PATH,
            Config.LICENSE_PLATE_MODEL_PATH
        )
        
        # Initialize tracker
        mot_tracker = Sort()
        results = {}
        
        # Load video
        video_path = os.environ.get('VIDEO_PATH', './f1.mp4')
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {video_path}")
        
        logger.info(f"Processing video: {video_path}")
        
        frame_nmr = -1
        ret = True
        
        while ret:
            frame_nmr += 1
            ret, frame = cap.read()
            
            if ret and frame_nmr % Config.FRAME_SKIP == 0:
                logger.info(f"Processing frame {frame_nmr}")
                results[frame_nmr] = {}
                
                # Detect vehicles
                detections = detector.detect_vehicles(frame, Config.VEHICLE_CLASS_IDS)
                
                if detections:
                    logger.debug(f"Detected {len(detections)} vehicles in frame {frame_nmr}")
                
                # Track vehicles
                tracking_data = np.array([[d[0], d[1], d[2], d[3], d[4]] for d in detections])
                track_ids = mot_tracker.update(tracking_data) if len(tracking_data) > 0 else np.array([])
                
                if len(track_ids) > 0:
                    logger.debug(f"Tracking {len(track_ids)} vehicles")
                
                # Detect license plates
                license_plates = detector.detect_license_plates(frame)
                
                if license_plates:
                    logger.debug(f"Detected {len(license_plates)} license plates")
                
                for license_plate in license_plates:
                    x1, y1, x2, y2, score, class_id = license_plate
                    
                    # Assign license plate to car
                    from util import get_car
                    xcar1, ycar1, xcar2, ycar2, car_id = get_car(license_plate, track_ids)
                    
                    if car_id != -1:
                        logger.info(f"Car ID: {car_id}, Detection confidence: {score:.2f}")
                        
                        # Process license plate
                        license_plate_text, text_score, plate_image = detector.process_license_plate(
                            frame,
                            license_plate
                        )
                        
                        if license_plate_text is not None:
                            logger.info(f"License Plate: {license_plate_text} (confidence: {text_score:.2f})")
                            
                            # Crop car image
                            car_image = frame[int(ycar1):int(ycar2), int(xcar1):int(xcar2), :]
                            
                            # Save images
                            try:
                                car_path, plate_path = save_detection_images(
                                    car_image,
                                    plate_image,
                                    license_plate_text,
                                    firebase_manager=firebase_manager
                                )
                                
                                # Store data in Firebase
                                import datetime
                                firebase_manager.push_data('users_detected', {
                                    'license_plate': license_plate_text,
                                    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'car_image': car_path,
                                    'plate_image': plate_path
                                })
                                
                                # Store results
                                results[frame_nmr][car_id] = {
                                    'car': {
                                        'bbox': [xcar1, ycar1, xcar2, ycar2],
                                        'score': score
                                    },
                                    'license_plate': {
                                        'bbox': [x1, y1, x2, y2],
                                        'text': license_plate_text,
                                        'bbox_score': score,
                                        'text_score': text_score
                                    }
                                }
                            except Exception as e:
                                logger.error(f"Error saving detection: {e}")
        
        cap.release()
        logger.info("Video processing completed")
        
        # Process flagged vehicles
        try:
            detected_data = firebase_manager.get_data('users_detected')
            database_data = firebase_manager.get_data('users_database')
            
            if detected_data and database_data:
                detected_plates = {
                    uid: details
                    for uid, details in detected_data.items()
                }
                database_plates = {
                    uid: entry.get('License_Plate')
                    for uid, entry in enumerate(database_data)
                    if 'License_Plate' in entry
                }
                
                process_flagged_vehicles(detected_plates, database_plates, firebase_manager)
        except Exception as e:
            logger.error(f"Error checking flagged vehicles: {e}")
        
        logger.info("Processing complete")
        
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
