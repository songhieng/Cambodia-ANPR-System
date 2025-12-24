"""
ANPR System Demo

Comprehensive demo script showing end-to-end processing on images and videos.
Displays results with visualizations and saves annotated outputs.

Usage:
    python demo.py --input path/to/image_or_video.mp4
    python demo.py --input path/to/image.jpg --output demo_outputs/
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import cv2
import numpy as np
from datetime import datetime

from anpr.utils.logger import setup_logger
from anpr.models.manager import ModelManager
from anpr.utils.config import Config
from anpr.core.ocr import OCREngine
from anpr.tracking.sort import Sort

# Setup logger
logger = setup_logger("demo", log_dir="logs")


class ANPRDemo:
    """ANPR system demonstrator for images and videos."""
    
    def __init__(self, output_dir: str = "demo_outputs"):
        """
        Initialize ANPR demo.
        
        Args:
            output_dir: Directory to save output files.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize model manager
        logger.info("Loading models...")
        self.model_manager = ModelManager()
        
        # Initialize OCR engine
        self.ocr_engine = OCREngine()
        
        # Load models
        self.vehicle_model = self.model_manager.load_model(
            'vehicle_detector',
            Config.YOLO_MODEL_PATH
        )
        self.plate_model = self.model_manager.load_model(
            'license_plate_detector',
            Config.LICENSE_PLATE_MODEL_PATH
        )
        self.type_model = self.model_manager.load_model(
            'vehicle_type_classifier',
            Config.CAR_TYPE_MODEL_PATH
        )
        self.color_model = self.model_manager.load_model(
            'vehicle_color_classifier',
            Config.CAR_COLOR_MODEL_PATH
        )
        
        if not all([self.vehicle_model, self.plate_model]):
            raise RuntimeError("Failed to load required models")
        
        logger.info("Models loaded successfully")
        
        # Initialize tracker
        self.tracker = Sort()
        
        # Statistics
        self.stats = {
            'frames_processed': 0,
            'vehicles_detected': 0,
            'plates_detected': 0,
            'plates_recognized': 0,
            'processing_time': 0.0
        }
    
    def _draw_detection(
        self,
        image: np.ndarray,
        bbox: List[float],
        label: str,
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2
    ) -> np.ndarray:
        """
        Draw bounding box and label on image.
        
        Args:
            image: Input image.
            bbox: Bounding box [x1, y1, x2, y2].
            label: Text label.
            color: Box color (BGR).
            thickness: Line thickness.
            
        Returns:
            Annotated image.
        """
        x1, y1, x2, y2 = map(int, bbox)
        
        # Draw rectangle
        cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
        
        # Draw label background
        (label_w, label_h), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
        )
        cv2.rectangle(
            image,
            (x1, y1 - label_h - 10),
            (x1 + label_w, y1),
            color,
            -1
        )
        
        # Draw label text
        cv2.putText(
            image,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )
        
        return image
    
    def process_frame(
        self,
        frame: np.ndarray,
        frame_idx: int = 0
    ) -> Tuple[np.ndarray, List[dict]]:
        """
        Process a single frame to detect vehicles and plates.
        
        Args:
            frame: Input frame.
            frame_idx: Frame index for tracking.
            
        Returns:
            Tuple of (annotated_frame, detections_list).
        """
        annotated = frame.copy()
        detections = []
        
        # Detect vehicles
        vehicle_results = self.vehicle_model(frame)[0]
        vehicle_detections = []
        
        for det in vehicle_results.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = det
            if int(class_id) in Config.VEHICLE_CLASS_IDS and score > 0.5:
                vehicle_detections.append([x1, y1, x2, y2, score, class_id])
        
        self.stats['vehicles_detected'] += len(vehicle_detections)
        
        # Track vehicles
        if vehicle_detections:
            tracking_data = np.array([[d[0], d[1], d[2], d[3], d[4]] for d in vehicle_detections])
            track_ids = self.tracker.update(tracking_data)
        else:
            track_ids = np.array([])
        
        # Draw vehicle boxes
        for track in track_ids:
            x1, y1, x2, y2, track_id = track
            self._draw_detection(
                annotated,
                [x1, y1, x2, y2],
                f"Vehicle {int(track_id)}",
                (255, 0, 0),
                2
            )
        
        # Detect license plates
        plate_results = self.plate_model(frame)[0]
        
        for plate_det in plate_results.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = plate_det
            
            if score < 0.5:
                continue
            
            self.stats['plates_detected'] += 1
            
            # Match plate to vehicle
            xcar1, ycar1, xcar2, ycar2, car_id = self.ocr_engine.get_vehicle_for_plate(plate_det, track_ids)
            
            if car_id != -1:
                # Extract and process plate
                plate_crop = frame[int(y1):int(y2), int(x1):int(x2), :]
                
                if plate_crop.size > 0:
                    plate_gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
                    _, plate_thresh = cv2.threshold(
                        plate_gray, 64, 255, cv2.THRESH_BINARY_INV
                    )
                    
                    # Read plate text
                    plate_text, text_score = self.ocr_engine.read_license_plate(plate_thresh)
                    
                    if plate_text:
                        self.stats['plates_recognized'] += 1
                        
                        # Classify vehicle
                        car_crop = frame[int(ycar1):int(ycar2), int(xcar1):int(xcar2), :]
                        
                        car_type = "Unknown"
                        car_color = "Unknown"
                        
                        if self.type_model and car_crop.size > 0:
                            try:
                                type_results = self.type_model(car_crop)
                                type_idx = type_results[0].probs.top5[0]
                                car_type = Config.VEHICLE_TYPE_MAP.get(type_idx, "Unknown")
                            except:
                                pass
                        
                        if self.color_model and car_crop.size > 0:
                            try:
                                color_results = self.color_model(car_crop)
                                color_idx = color_results[0].probs.top5[0]
                                car_color = Config.VEHICLE_COLOR_MAP.get(color_idx, "Unknown")
                            except:
                                pass
                        
                        # Draw plate box
                        label = f"{plate_text} ({text_score:.2f})"
                        self._draw_detection(
                            annotated,
                            [x1, y1, x2, y2],
                            label,
                            (0, 255, 0),
                            2
                        )
                        
                        # Store detection
                        detections.append({
                            'frame': frame_idx,
                            'vehicle_id': int(car_id),
                            'license_plate': plate_text,
                            'confidence': float(text_score),
                            'vehicle_type': car_type,
                            'vehicle_color': car_color,
                            'bbox': [int(x1), int(y1), int(x2), int(y2)]
                        })
                        
                        logger.info(
                            f"Frame {frame_idx}: Detected {car_color} {car_type} "
                            f"with plate {plate_text} (conf: {text_score:.2f})"
                        )
        
        self.stats['frames_processed'] += 1
        return annotated, detections
    
    def process_image(self, image_path: str) -> str:
        """
        Process a single image.
        
        Args:
            image_path: Path to input image.
            
        Returns:
            Path to output image.
        """
        logger.info(f"Processing image: {image_path}")
        
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to read image: {image_path}")
        
        start_time = datetime.now()
        
        # Process frame
        annotated, detections = self.process_frame(image, 0)
        
        self.stats['processing_time'] = (datetime.now() - start_time).total_seconds()
        
        # Save annotated image
        output_name = f"annotated_{Path(image_path).stem}.jpg"
        output_path = self.output_dir / output_name
        cv2.imwrite(str(output_path), annotated)
        
        logger.info(f"Saved annotated image: {output_path}")
        
        # Print results
        self._print_results(detections)
        
        return str(output_path)
    
    def process_video(
        self,
        video_path: str,
        frame_skip: int = None,
        max_frames: int = None
    ) -> str:
        """
        Process a video file.
        
        Args:
            video_path: Path to input video.
            frame_skip: Process every Nth frame (default: Config.FRAME_SKIP).
            max_frames: Maximum frames to process (None = all).
            
        Returns:
            Path to output video.
        """
        logger.info(f"Processing video: {video_path}")
        
        if frame_skip is None:
            frame_skip = Config.FRAME_SKIP
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {video_path}")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"Video: {width}x{height} @ {fps}fps, {total_frames} frames")
        
        # Setup output video
        output_name = f"annotated_{Path(video_path).stem}.mp4"
        output_path = self.output_dir / output_name
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        start_time = datetime.now()
        all_detections = []
        frame_idx = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if max_frames and frame_idx >= max_frames:
                    break
                
                # Process every Nth frame
                if frame_idx % frame_skip == 0:
                    annotated, detections = self.process_frame(frame, frame_idx)
                    all_detections.extend(detections)
                    out.write(annotated)
                    
                    if frame_idx % (frame_skip * 10) == 0:
                        logger.info(f"Processed {frame_idx}/{total_frames} frames")
                else:
                    out.write(frame)
                
                frame_idx += 1
        
        finally:
            cap.release()
            out.release()
        
        self.stats['processing_time'] = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Saved annotated video: {output_path}")
        
        # Print results
        self._print_results(all_detections)
        
        return str(output_path)
    
    def _print_results(self, detections: List[dict]):
        """Print detection results and statistics."""
        print("\n" + "=" * 70)
        print("DETECTION RESULTS")
        print("=" * 70)
        
        if detections:
            print(f"\nDetected {len(detections)} license plates:\n")
            for i, det in enumerate(detections, 1):
                print(f"{i}. Plate: {det['license_plate']} (confidence: {det['confidence']:.2f})")
                print(f"   Vehicle: {det['vehicle_color']} {det['vehicle_type']}")
                print(f"   Frame: {det['frame']}, Vehicle ID: {det['vehicle_id']}")
                print()
        else:
            print("\nNo license plates detected.")
        
        print("\n" + "=" * 70)
        print("STATISTICS")
        print("=" * 70)
        print(f"Frames processed: {self.stats['frames_processed']}")
        print(f"Vehicles detected: {self.stats['vehicles_detected']}")
        print(f"Plates detected: {self.stats['plates_detected']}")
        print(f"Plates recognized: {self.stats['plates_recognized']}")
        print(f"Processing time: {self.stats['processing_time']:.2f}s")
        if self.stats['frames_processed'] > 0:
            fps = self.stats['frames_processed'] / self.stats['processing_time']
            print(f"Processing speed: {fps:.2f} fps")
        print("=" * 70)


def main():
    """Main demo execution."""
    parser = argparse.ArgumentParser(
        description="ANPR System Demo - Process images or videos"
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help="Path to input image or video file"
    )
    parser.add_argument(
        '--output', '-o',
        default='demo_outputs',
        help="Output directory for results (default: demo_outputs)"
    )
    parser.add_argument(
        '--frame-skip',
        type=int,
        default=None,
        help=f"Process every Nth frame for videos (default: {Config.FRAME_SKIP})"
    )
    parser.add_argument(
        '--max-frames',
        type=int,
        default=None,
        help="Maximum frames to process (default: all)"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Determine file type
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    
    file_ext = input_path.suffix.lower()
    
    try:
        # Initialize demo
        demo = ANPRDemo(output_dir=args.output)
        
        # Process based on file type
        if file_ext in video_extensions:
            logger.info("Detected video file")
            output = demo.process_video(
                str(input_path),
                frame_skip=args.frame_skip,
                max_frames=args.max_frames
            )
        elif file_ext in image_extensions:
            logger.info("Detected image file")
            output = demo.process_image(str(input_path))
        else:
            logger.error(f"Unsupported file type: {file_ext}")
            logger.info(f"Supported: {video_extensions | image_extensions}")
            sys.exit(1)
        
        print(f"\n✓ Processing complete!")
        print(f"✓ Output saved to: {output}")
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
