"""
Enhanced Gradio Web Interface for ANPR System

Provides user-friendly interface for video upload and processing.
Displays results with statistics and vehicle information.

Usage:
    python deploy.py
"""

import os
import logging
from typing import Dict, Any, List, Tuple
import cv2
import numpy as np
import gradio as gr
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

from anpr.tracking.sort import Sort
from anpr.utils.config import Config
from anpr.integrations.firebase import get_firebase_manager
from anpr.models.manager import ModelManager
from anpr.utils.logger import setup_logger
from anpr.core.ocr import OCREngine

# Setup logging
logger = setup_logger("deploy", log_dir="logs")

# Load environment variables
load_dotenv()

# Initialize Firebase
firebase_manager = None
try:
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
    
    if os.path.exists(credentials_path):
        firebase_manager.initialize(credentials_path, database_url, storage_bucket)
        logger.info("Firebase initialized successfully")
    else:
        logger.warning("Firebase credentials not found, running without Firebase")
        firebase_manager = None
except Exception as e:
    logger.warning(f"Firebase initialization failed: {e}. Running without Firebase.")
    firebase_manager = None


def get_flagged_plates() -> List[str]:
    """Retrieve flagged license plates from Firebase."""
    if not firebase_manager:
        return []
    
    try:
        detected_data = firebase_manager.get_data('Detected')
        if detected_data:
            return [data['plate'] for data in detected_data.values() if 'plate' in data]
        return []
    except Exception as e:
        logger.error(f"Error retrieving flagged plates: {e}")
        return []


def process_video(video_path: str) -> Tuple[str, pd.DataFrame]:
    """
    Process a video file to detect vehicles and license plates.
    
    Args:
        video_path: Path to the video file to process.
        
    Returns:
        Tuple of (results_text, detections_dataframe).
    """
    try:
        # Get flagged plates
        flagged_plates = get_flagged_plates()
        logger.info(f"Loaded {len(flagged_plates)} flagged plates")
        
        # Ensure directories exist
        Config.ensure_directories()
        
        # Load models
        model_manager = ModelManager()
        ocr_engine = OCREngine()
        vehicle_model = model_manager.load_model('vehicle_detector', Config.YOLO_MODEL_PATH)
        plate_model = model_manager.load_model('license_plate_detector', Config.LICENSE_PLATE_MODEL_PATH)
        type_model = model_manager.load_model('vehicle_type_classifier', Config.CAR_TYPE_MODEL_PATH)
        color_model = model_manager.load_model('vehicle_color_classifier', Config.CAR_COLOR_MODEL_PATH)
        
        if not all([vehicle_model, plate_model]):
            return "Error: Failed to load required models", pd.DataFrame()
        
        # Initialize tracker
        mot_tracker = Sort()
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return f"Error: Failed to open video file: {video_path}", pd.DataFrame()
        
        logger.info(f"Processing video: {video_path}")
        
        # Statistics
        frame_count = 0
        all_detections = []
        vehicle_counts = {v: 0 for v in Config.COCO_CLASS_TO_VEHICLE.values()}
        track_id_to_class_id = {}
        unique_vehicle_ids = set()
        flagged_count = 0
        
        ret = True
        
        while ret:
            frame_count += 1
            ret, frame = cap.read()
            
            if ret and frame_count % Config.FRAME_SKIP == 0:
                logger.info(f"Processing frame {frame_count}")
                
                # Detect vehicles
                vehicle_results = vehicle_model(frame)[0]
                vehicle_detections = []
                
                for det in vehicle_results.boxes.data.tolist():
                    x1, y1, y2, x2, score, class_id = det
                    if int(class_id) in Config.VEHICLE_CLASS_IDS and score > 0.5:
                        vehicle_detections.append([x1, y1, x2, y2, score, class_id])
                
                # Track vehicles
                if vehicle_detections:
                    tracking_data = np.array([[d[0], d[1], d[2], d[3], d[4]] for d in vehicle_detections])
                    track_ids = mot_tracker.update(tracking_data)
                    
                    for track in track_ids:
                        track_id = int(track[4])
                        unique_vehicle_ids.add(track_id)
                        
                        for d in vehicle_detections:
                            if all([np.isclose(track[i], d[i], atol=1e-3) for i in range(4)]):
                                track_id_to_class_id[track_id] = d[5]
                                break
                else:
                    track_ids = np.array([])
                
                # Detect license plates
                plate_results = plate_model(frame)[0]
                
                for plate_det in plate_results.boxes.data.tolist():
                    x1, y1, x2, y2, score, class_id = plate_det
                    
                    if score < 0.5:
                        continue
                    
                    xcar1, ycar1, xcar2, ycar2, car_id = ocr_engine.get_vehicle_for_plate(plate_det, track_ids)
                    
                    if car_id != -1:
                        plate_crop = frame[int(y1):int(y2), int(x1):int(x2), :]
                        
                        if plate_crop.size > 0:
                            plate_gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
                            _, plate_thresh = cv2.threshold(plate_gray, 64, 255, cv2.THRESH_BINARY_INV)
                            
                            plate_text, text_score = ocr_engine.read_license_plate(plate_thresh)
                            
                            if plate_text:
                                is_flagged = plate_text in flagged_plates
                                if is_flagged:
                                    flagged_count += 1
                                
                                car_image = frame[int(ycar1):int(ycar2), int(xcar1):int(xcar2), :]
                                    
                                car_type = "Unknown"
                                car_color = "Unknown"
                                
                                if type_model and car_image.size > 0:
                                    try:
                                        type_results = type_model(car_image)
                                        type_idx = type_results[0].probs.top5[0]
                                        car_type = Config.VEHICLE_TYPE_MAP.get(type_idx, "Unknown")
                                    except:
                                        pass
                                
                                if color_model and car_image.size > 0:
                                    try:
                                        color_results = color_model(car_image)
                                        color_idx = color_results[0].probs.top5[0]
                                        car_color = Config.VEHICLE_COLOR_MAP.get(color_idx, "Unknown")
                                    except:
                                        pass
                                
                                all_detections.append({
                                    'Frame': frame_count,
                                    'License Plate': plate_text,
                                    'Confidence': f"{text_score:.2f}",
                                    'Vehicle Type': car_type,
                                    'Vehicle Color': car_color,
                                    'Flagged': '⚠️ YES' if is_flagged else 'No'
                                })
                                
                                logger.info(f"Detected: {car_color} {car_type} - {plate_text}")
                                
                                # Save to Firebase if available and flagged
                                if firebase_manager and is_flagged:
                                    try:
                                        timestamp_str = datetime.now().isoformat()
                                        firebase_manager.push_data('flagged_detections', {
                                            'license_plate': plate_text,
                                            'timestamp': timestamp_str,
                                            'vehicle_type': car_type,
                                            'vehicle_color': car_color
                                        })
                                    except Exception as e:
                                        logger.error(f"Firebase error: {e}")
        
        cap.release()
        
        # Calculate vehicle counts
        for class_id in track_id_to_class_id.values():
            vehicle_type = Config.COCO_CLASS_TO_VEHICLE.get(class_id, 'unknown')
            if vehicle_type in vehicle_counts:
                vehicle_counts[vehicle_type] += 1
        
        # Calculate traffic score
        traffic_score = 1 + sum(count * 4 for count in vehicle_counts.values())
        
        # Build result string
        result_lines = [
            "═" * 60,
            "✓ VIDEO PROCESSING COMPLETE",
            "═" * 60,
            f"📊 Total frames processed: {frame_count}",
            f"🚗 Unique vehicles tracked: {len(unique_vehicle_ids)}",
            f"🔢 License plates detected: {len(all_detections)}",
            f"⚠️  Flagged vehicles: {flagged_count}",
            f"📈 Traffic score: {traffic_score}",
            "",
            "🚙 Vehicle Type Breakdown:",
        ]
        
        for vehicle_type, count in vehicle_counts.items():
            if count > 0:
                result_lines.append(f"   • {vehicle_type.capitalize()}: {count}")
        
        result_lines.append("═" * 60)
        
        logger.info("Video processing completed successfully")
        
        df = pd.DataFrame(all_detections) if all_detections else pd.DataFrame()
        
        return "\n".join(result_lines), df
        
    except Exception as e:
        error_msg = f"❌ Error processing video: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg, pd.DataFrame()


def create_interface():
    """Create and configure the Gradio interface."""
    
    with gr.Blocks(title="Cambodia ANPR System", theme=gr.themes.Soft()) as interface:
        gr.Markdown(
            """
            # 🚗 Cambodia ANPR System
            ### Automatic Number Plate Recognition with Vehicle Classification
            
            Upload a video to detect and track vehicles, recognize license plates, and identify vehicle types and colors.
            """
        )
        
        with gr.Row():
            with gr.Column():
                video_input = gr.Video(label="📤 Upload Video File")
                process_btn = gr.Button("🚀 Process Video", variant="primary", size="lg")
            
            with gr.Column():
                results_text = gr.Textbox(
                    label="📊 Processing Results",
                    lines=15,
                    max_lines=20
                )
        
        results_df = gr.Dataframe(
            label="🔍 Detected License Plates",
            headers=["Frame", "License Plate", "Confidence", "Vehicle Type", "Vehicle Color", "Flagged"],
            interactive=False
        )
        
        gr.Markdown(
            """
            ---
            **Features:**
            - ✅ Real-time vehicle detection and tracking
            - ✅ License plate recognition with OCR
            - ✅ Vehicle type classification (Sedan, SUV, etc.)
            - ✅ Vehicle color detection
            - ✅ Automatic flagging of suspicious plates
            - ✅ Traffic analysis and scoring
            """
        )
        
        process_btn.click(
            fn=process_video,
            inputs=[video_input],
            outputs=[results_text, results_df]
        )
    
    return interface


if __name__ == "__main__":
    logger.info("Starting Gradio interface...")
    interface = create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        show_error=True
    )
