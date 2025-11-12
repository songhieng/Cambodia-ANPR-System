"""
Gradio web interface for vehicle and license plate detection.
Provides an easy-to-use interface for uploading and processing videos.
"""

import os
import logging
from typing import Dict, Any, List
import cv2
import numpy as np
import gradio as gr
from dotenv import load_dotenv

from sort.sort import Sort
from config import Config
from firebase_utils import get_firebase_manager
from detection_utils import (
    VehicleDetector,
    save_detection_images,
    check_flagged_plate
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def initialize_firebase() -> Any:
    """
    Initialize Firebase connection.
    
    Returns:
        Firebase manager instance.
    """
    firebase_manager = get_firebase_manager()
    
    credentials_path = os.environ.get(
        'FIREBASE_CREDENTIALS_PATH',
        'anpr-v3-b5bb8-firebase-adminsdk-8pkgt-d88b8f69b1.json'
    )
    database_url = os.environ.get(
        'FIREBASE_DATABASE_URL',
        'https://anpr-v3-b5bb8-default-rtdb.asia-southeast1.firebasedatabase.app'
    )
    storage_bucket = os.environ.get(
        'FIREBASE_STORAGE_BUCKET',
        'anpr-v3-b5bb8.appspot.com'
    )
    
    firebase_manager.initialize(credentials_path, database_url, storage_bucket)
    return firebase_manager


def get_flagged_plates(firebase_manager) -> List[str]:
    """
    Retrieve flagged license plates from Firebase.
    
    Args:
        firebase_manager: Firebase manager instance.
        
    Returns:
        List of flagged license plate numbers.
    """
    try:
        detected_data = firebase_manager.get_data('Detected')
        if detected_data:
            return [data['plate'] for data in detected_data.values() if 'plate' in data]
        return []
    except Exception as e:
        logger.error(f"Error retrieving flagged plates: {e}")
        return []


def process_video(video_path: str) -> str:
    """
    Process a video file to detect vehicles and license plates.
    
    Args:
        video_path: Path to the video file to process.
        
    Returns:
        String containing processing results and statistics.
    """
    try:
        # Initialize Firebase
        firebase_manager = initialize_firebase()
        
        # Get flagged plates
        flagged_plates = get_flagged_plates(firebase_manager)
        logger.info(f"Loaded {len(flagged_plates)} flagged plates")
        
        # Ensure directories exist
        Config.ensure_directories()
        
        # Initialize detector with all models
        detector = VehicleDetector(
            Config.YOLO_MODEL_PATH,
            Config.LICENSE_PLATE_MODEL_PATH,
            Config.CAR_TYPE_MODEL_PATH,
            Config.CAR_COLOR_MODEL_PATH
        )
        
        # Initialize tracker
        mot_tracker = Sort()
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return f"Error: Failed to open video file: {video_path}"
        
        logger.info(f"Processing video: {video_path}")
        
        # Statistics
        frame_count = 0
        detected_plates_count = 0
        flagged_count = 0
        vehicle_counts = {v: 0 for v in Config.COCO_CLASS_TO_VEHICLE.values()}
        track_id_to_class_id = {}
        unique_vehicle_ids = set()
        traffic_score = 1
        
        ret = True
        frame_rate = cap.get(cv2.CAP_PROP_FPS)
        
        while ret:
            frame_count += 1
            ret, frame = cap.read()
            
            if ret and frame_count % Config.FRAME_SKIP == 0:
                logger.info(f"Processing frame {frame_count}")
                
                # Detect vehicles
                detections = detector.detect_vehicles(frame, Config.VEHICLE_CLASS_IDS)
                
                # Track vehicles
                if detections:
                    tracking_data = np.array([[d[0], d[1], d[2], d[3], d[4]] for d in detections])
                    track_ids = mot_tracker.update(tracking_data)
                    
                    # Update vehicle tracking
                    for track in track_ids:
                        track_id = int(track[4])
                        unique_vehicle_ids.add(track_id)
                        
                        # Match track to class
                        for d in detections:
                            if all([np.isclose(track[i], d[i], atol=1e-3) for i in range(4)]):
                                track_id_to_class_id[track_id] = d[5]
                                break
                else:
                    track_ids = np.array([])
                
                # Detect license plates
                license_plates = detector.detect_license_plates(frame)
                
                for license_plate in license_plates:
                    x1, y1, x2, y2, score, class_id = license_plate
                    
                    # Assign to car
                    from util import get_car
                    xcar1, ycar1, xcar2, ycar2, car_id = get_car(license_plate, track_ids)
                    
                    if car_id != -1:
                        # Process license plate
                        license_plate_text, text_score, plate_image = detector.process_license_plate(
                            frame,
                            license_plate
                        )
                        
                        if license_plate_text is not None:
                            detected_plates_count += 1
                            logger.info(f"Detected plate: {license_plate_text}")
                            
                            # Check if flagged
                            is_flagged = check_flagged_plate(license_plate_text, flagged_plates)
                            if is_flagged:
                                flagged_count += 1
                                logger.warning(f"FLAGGED PLATE DETECTED: {license_plate_text}")
                            
                            # Crop car image
                            car_image = frame[int(ycar1):int(ycar2), int(xcar1):int(xcar2), :]
                            
                            # Classify vehicle
                            car_type, type_confidence = detector.classify_vehicle_type(car_image)
                            car_color, color_confidence = detector.classify_vehicle_color(car_image)
                            
                            logger.info(f"Vehicle: {car_color} {car_type}")
                            
                            # Save images
                            try:
                                save_detection_images(
                                    car_image,
                                    plate_image,
                                    license_plate_text,
                                    car_type,
                                    car_color,
                                    firebase_manager
                                )
                                
                                # Save to special DATA folder if flagged
                                if is_flagged:
                                    import datetime
                                    timestamp_str = datetime.datetime.utcnow().replace(
                                        microsecond=0
                                    ).isoformat()
                                    timestamp_int = int(
                                        datetime.datetime.utcnow().timestamp() * 1000
                                    )
                                    
                                    flagged_filename = f"car_{license_plate_text}_{timestamp_str}_{timestamp_int}.jpg"
                                    flagged_path = os.path.join(Config.DATA_OUTPUT_DIR, flagged_filename)
                                    cv2.imwrite(flagged_path, car_image)
                                    
                                    firebase_manager.upload_to_storage(
                                        flagged_path,
                                        f"DATA/{flagged_filename}"
                                    )
                            except Exception as e:
                                logger.error(f"Error saving detection: {e}")
        
        cap.release()
        
        # Calculate vehicle counts
        for class_id in track_id_to_class_id.values():
            vehicle_type = Config.COCO_CLASS_TO_VEHICLE.get(class_id, 'unknown')
            if vehicle_type in vehicle_counts:
                vehicle_counts[vehicle_type] += 1
        
        # Calculate traffic score
        for vehicle_type, count in vehicle_counts.items():
            traffic_score += count * 4
            
            # Upload counts to Firebase
            firebase_manager.push_data('right', {
                'text1': vehicle_type,
                'text2': count
            })
        
        # Upload traffic score
        firebase_manager.set_data('TrafficScore1', traffic_score)
        
        # Build result string
        result_lines = [
            "=== Video Processing Complete ===",
            f"Total frames processed: {frame_count}",
            f"License plates detected: {detected_plates_count}",
            f"Flagged vehicles: {flagged_count}",
            f"Traffic score: {traffic_score}",
            "",
            "Vehicle counts:"
        ]
        
        for vehicle_type, count in vehicle_counts.items():
            result_lines.append(f"  {vehicle_type}: {count}")
        
        logger.info("Video processing completed successfully")
        return "\n".join(result_lines)
        
    except Exception as e:
        error_msg = f"Error processing video: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


def create_interface():
    """Create and configure the Gradio interface."""
    interface = gr.Interface(
        fn=process_video,
        inputs=gr.Video(label="Upload Video"),
        outputs=gr.Textbox(label="Processing Results", lines=10),
        title="Cambodia ANPR System - Vehicle and License Plate Detection",
        description=(
            "Upload a video to detect vehicles and license plates. "
            "The system will identify vehicle types, colors, and flag suspicious plates."
        ),
        examples=[],
        allow_flagging="never"
    )
    return interface


if __name__ == "__main__":
    logger.info("Starting Gradio interface...")
    interface = create_interface()
    interface.launch(share=True)
