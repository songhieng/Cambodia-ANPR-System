"""
Enhanced Streamlit Web Interface for ANPR System

Modern web interface with real-time processing, visualization, and analytics.
Provides comprehensive monitoring and results display.

Usage:
    streamlit run app_streamlit.py
"""

import streamlit as st
import cv2
import numpy as np
from pathlib import Path
import tempfile
from datetime import datetime
import pandas as pd
from typing import List, Dict, Any

from anpr.utils.logger import setup_logger
from anpr.models.manager import ModelManager
from anpr.utils.config import Config
from anpr.core.ocr import OCREngine
from anpr.tracking.sort import Sort

# Configure page
st.set_page_config(
    page_title="Cambodia ANPR System",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

logger = setup_logger("streamlit_app")


@st.cache_resource
def initialize_models():
    """Initialize and cache models."""
    with st.spinner("Loading AI models..."):
        manager = ModelManager()
        ocr_engine = OCREngine()
        
        vehicle_model = manager.load_model('vehicle_detector', Config.YOLO_MODEL_PATH)
        plate_model = manager.load_model('license_plate_detector', Config.LICENSE_PLATE_MODEL_PATH)
        type_model = manager.load_model('vehicle_type_classifier', Config.CAR_TYPE_MODEL_PATH)
        color_model = manager.load_model('vehicle_color_classifier', Config.CAR_COLOR_MODEL_PATH)
        
        if not all([vehicle_model, plate_model]):
            st.error("Failed to load required models!")
            st.stop()
        
        logger.info("Models loaded successfully")
        return vehicle_model, plate_model, type_model, color_model, ocr_engine


def process_frame(frame, vehicle_model, plate_model, type_model, color_model, ocr_engine, tracker):
    """Process a single frame."""
    detections = []
    
    # Detect vehicles
    vehicle_results = vehicle_model(frame)[0]
    vehicle_detections = []
    
    for det in vehicle_results.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = det
        if int(class_id) in Config.VEHICLE_CLASS_IDS and score > 0.5:
            vehicle_detections.append([x1, y1, x2, y2, score, class_id])
    
    # Track vehicles
    if vehicle_detections:
        tracking_data = np.array([[d[0], d[1], d[2], d[3], d[4]] for d in vehicle_detections])
        track_ids = tracker.update(tracking_data)
    else:
        track_ids = np.array([])
    
    # Detect plates
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
                    car_crop = frame[int(ycar1):int(ycar2), int(xcar1):int(xcar2), :]
                    
                    car_type = "Unknown"
                    car_color = "Unknown"
                    
                    if type_model and car_crop.size > 0:
                        try:
                            type_results = type_model(car_crop)
                            type_idx = type_results[0].probs.top5[0]
                            car_type = Config.VEHICLE_TYPE_MAP.get(type_idx, "Unknown")
                        except:
                            pass
                    
                    if color_model and car_crop.size > 0:
                        try:
                            color_results = color_model(car_crop)
                            color_idx = color_results[0].probs.top5[0]
                            car_color = Config.VEHICLE_COLOR_MAP.get(color_idx, "Unknown")
                        except:
                            pass
                    
                    detections.append({
                        'license_plate': plate_text,
                        'confidence': float(text_score),
                        'vehicle_type': car_type,
                        'vehicle_color': car_color,
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'vehicle_bbox': [int(xcar1), int(ycar1), int(xcar2), int(ycar2)]
                    })
    
    return detections


def draw_detections(frame, detections):
    """Draw detections on frame."""
    annotated = frame.copy()
    
    for det in detections:
        # Draw vehicle box (blue)
        vx1, vy1, vx2, vy2 = det['vehicle_bbox']
        cv2.rectangle(annotated, (vx1, vy1), (vx2, vy2), (255, 0, 0), 2)
        
        # Draw plate box (green)
        x1, y1, x2, y2 = det['bbox']
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Draw label
        label = f"{det['license_plate']} ({det['confidence']:.2f})"
        cv2.putText(annotated, label, (x1, y1 - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    return annotated


def main():
    """Main Streamlit app."""
    st.title("🚗 Cambodia ANPR System")
    st.markdown("### Automatic Number Plate Recognition with Vehicle Classification")
    
    # Sidebar
    st.sidebar.header("⚙️ Settings")
    
    processing_mode = st.sidebar.radio(
        "Processing Mode",
        ["Image", "Video"],
        help="Select input type"
    )
    
    confidence_threshold = st.sidebar.slider(
        "Detection Confidence",
        min_value=0.3,
        max_value=0.95,
        value=0.5,
        step=0.05,
        help="Minimum confidence for detections"
    )
    
    if processing_mode == "Video":
        frame_skip = st.sidebar.slider(
            "Frame Skip",
            min_value=1,
            max_value=100,
            value=Config.FRAME_SKIP,
            help="Process every Nth frame"
        )
    
    # Initialize models
    vehicle_model, plate_model, type_model, color_model, ocr_engine = initialize_models()
    
    st.sidebar.success("✓ Models loaded successfully")
    
    # File uploader
    st.header("📤 Upload File")
    
    if processing_mode == "Image":
        uploaded_file = st.file_uploader(
            "Choose an image",
            type=['jpg', 'jpeg', 'png'],
            help="Upload an image containing vehicles"
        )
    else:
        uploaded_file = st.file_uploader(
            "Choose a video",
            type=['mp4', 'avi', 'mov'],
            help="Upload a video file"
        )
    
    if uploaded_file is not None:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name
        
        if processing_mode == "Image":
            # Process image
            st.header("🔍 Processing Image")
            
            image = cv2.imread(tmp_path)
            
            with st.spinner("Detecting vehicles and license plates..."):
                tracker = Sort()
                detections = process_frame(
                    image, vehicle_model, plate_model,
                    type_model, color_model, ocr_engine, tracker
                )
                annotated = draw_detections(image, detections)
            
            # Display results
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Original Image")
                st.image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), use_container_width=True)
            
            with col2:
                st.subheader("Detected Results")
                st.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), use_container_width=True)
            
            # Results table
            if detections:
                st.header("📊 Detection Results")
                
                df = pd.DataFrame(detections)
                df = df[['license_plate', 'confidence', 'vehicle_type', 'vehicle_color']]
                df.columns = ['License Plate', 'Confidence', 'Vehicle Type', 'Vehicle Color']
                
                st.dataframe(df, use_container_width=True)
                
                # Statistics
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Vehicles", len(detections))
                col2.metric("Avg Confidence", f"{df['Confidence'].mean():.2f}")
                col3.metric("Unique Plates", df['License Plate'].nunique())
            else:
                st.warning("No vehicles or license plates detected.")
        
        else:
            # Process video
            st.header("🎥 Processing Video")
            
            cap = cv2.VideoCapture(tmp_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            st.info(f"Video: {total_frames} frames @ {fps} FPS")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            tracker = Sort()
            all_detections = []
            frame_idx = 0
            
            # Output video setup
            output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    if frame_idx % frame_skip == 0:
                        detections = process_frame(
                            frame, vehicle_model, plate_model,
                            type_model, color_model, ocr_engine, tracker
                        )
                        all_detections.extend(detections)
                        annotated = draw_detections(frame, detections)
                        out.write(annotated)
                    else:
                        out.write(frame)
                    
                    frame_idx += 1
                    progress = frame_idx / total_frames
                    progress_bar.progress(progress)
                    status_text.text(f"Processing frame {frame_idx}/{total_frames}")
            
            finally:
                cap.release()
                out.release()
            
            progress_bar.progress(1.0)
            status_text.text("✓ Processing complete!")
            
            # Display results
            if all_detections:
                st.header("📊 Detection Results")
                
                df = pd.DataFrame(all_detections)
                df = df[['license_plate', 'confidence', 'vehicle_type', 'vehicle_color']]
                df.columns = ['License Plate', 'Confidence', 'Vehicle Type', 'Vehicle Color']
                
                # Aggregate by unique plates
                summary = df.groupby('License Plate').agg({
                    'Confidence': 'mean',
                    'Vehicle Type': 'first',
                    'Vehicle Color': 'first'
                }).reset_index()
                
                st.dataframe(summary, use_container_width=True)
                
                # Statistics
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Detections", len(all_detections))
                col2.metric("Unique Plates", summary.shape[0])
                col3.metric("Frames Processed", frame_idx)
                col4.metric("Avg Confidence", f"{df['Confidence'].mean():.2f}")
                
                # Download processed video
                with open(output_path, 'rb') as f:
                    st.download_button(
                        label="📥 Download Processed Video",
                        data=f,
                        file_name=f"anpr_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                        mime="video/mp4"
                    )
            else:
                st.warning("No vehicles or license plates detected in the video.")


if __name__ == "__main__":
    main()
