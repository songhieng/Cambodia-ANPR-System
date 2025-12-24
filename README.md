# Cambodia ANPR System 🚗

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)]()

**Production-ready Automatic Number Plate Recognition (ANPR) system** powered by YOLOv8 and EasyOCR. Detects vehicles, recognizes license plates, classifies vehicle types and colors, with optional Firebase integration for cloud storage and watchlist monitoring.

---

## 📋 Table of Contents

- [Features](#-features)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Modes](#-usage-modes)
- [Configuration](#-configuration)
- [How It Works](#-how-it-works)
- [Model Information](#-model-information)
- [Firebase Integration](#-firebase-integration)
- [Development](#-development)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

---

## ✨ Features

- **🎯 Multi-Stage Detection Pipeline**
  - Vehicle detection using YOLOv8 (COCO pretrained)
  - License plate detection with custom-trained model
  - Real-time object tracking with SORT algorithm

- **🔤 OCR & Recognition**
  - Robust license plate text recognition with EasyOCR
  - Character mapping and format validation
  - Confidence scoring for detections

- **🚙 Vehicle Classification**
  - Type classification: Sedan, SUV, Coupe, Hatchback, Pickup, Convertible
  - Color detection: 15 distinct colors including black, white, red, blue, etc.

- **☁️ Cloud Integration**
  - Optional Firebase Realtime Database
  - Firebase Storage for detected images
  - Watchlist monitoring and flagged vehicle alerts

- **🖥️ Multiple Interfaces**
  - **CLI**: Command-line processing for automation
  - **Gradio Web UI**: Interactive web interface with rich visualizations
  - **Streamlit Dashboard**: Modern analytics dashboard
  - **Demo Script**: Standalone testing with annotated outputs

- **📊 Production Features**
  - Centralized logging with daily rotation
  - Model version management and caching
  - Comprehensive error handling
  - Configurable via environment variables
  - Unit test coverage

---

## 📁 Project Structure

```
Cambodia-ANPR-System/
├── anpr/                          # Main ANPR package
│   ├── __init__.py
│   ├── core/                      # Core detection logic
│   │   ├── __init__.py
│   │   ├── detector.py           # Unified ANPR detector
│   │   └── ocr.py                # OCR engine & plate recognition
│   ├── models/                    # Model management
│   │   ├── __init__.py
│   │   ├── manager.py            # Model loading & caching
│   │   └── weights/              # Model weight files (.pt)
│   │       ├── yolov8n.pt        # Vehicle detection (COCO)
│   │       ├── run46.pt          # License plate detection
│   │       ├── car.pt            # Vehicle type classifier
│   │       ├── color.pt          # Vehicle color classifier
│   │       └── make.pt           # Vehicle make classifier
│   ├── integrations/              # External service integrations
│   │   ├── __init__.py
│   │   └── firebase.py           # Firebase manager
│   ├── utils/                     # Utilities
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration management
│   │   └── logger.py             # Logging setup
│   └── tracking/                  # Object tracking
│       ├── __init__.py
│       └── sort.py               # SORT tracking algorithm
│
├── apps/                          # Application entry points
│   ├── __init__.py
│   ├── cli.py                    # CLI application
│   ├── web_gradio.py             # Gradio web interface
│   ├── web_streamlit.py          # Streamlit dashboard
│   └── demo.py                   # Demo/testing script
│
├── tests/                         # Unit tests
│   ├── __init__.py
│   ├── test_detector.py
│   ├── test_ocr.py
│   ├── test_models.py
│   └── run_tests.py
│
├── config/                        # Configuration files
│   ├── .env.example              # Environment template
│   └── (firebase-credentials.json) # Place credentials here
│
├── outputs/                       # All system outputs
│   ├── detected_cars/            # Vehicle images
│   ├── detected_plates/          # Plate images
│   ├── demo_results/             # Demo outputs
│   └── flagged/                  # Flagged vehicle data
│
├── logs/                          # Application logs
│   └── anpr_YYYYMMDD.log        # Daily log files
│
├── .gitignore                     # Git ignore rules
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── setup.py                       # Package installation
└── .env                          # Environment config (create from .env.example)
```

---

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- CUDA (optional, for GPU acceleration)
- Webcam or video files for processing

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/Cambodia-ANPR-System.git
cd Cambodia-ANPR-System
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt

# Or install as package
pip install -e .
```

### Step 4: Download Model Weights

Place the following model files in `anpr/models/weights/`:
- `yolov8n.pt` - Vehicle detection ([Download](https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt))
- `run46.pt` - License plate detection (custom trained)
- `car.pt` - Vehicle type classifier (custom trained)
- `color.pt` - Vehicle color classifier (custom trained)

### Step 5: Configure Environment

```bash
# Copy environment template
cp config/.env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

---

## ⚡ Quick Start

### 1. CLI Processing (Recommended for Production)

```bash
# Process video with all features
python -m apps.cli --video path/to/video.mp4

# Process without Firebase
python -m apps.cli --video video.mp4 --no-firebase

# Or if installed as package
anpr-cli --video video.mp4
```

### 2. Demo Script (Best for Testing)

```bash
# Process image
python apps/demo.py --input image.jpg --output results/

# Process video with annotations
python apps/demo.py --input video.mp4
```

### 3. Gradio Web Interface (User-Friendly)

```bash
python apps/web_gradio.py
# Open browser to http://localhost:7860
```

### 4. Streamlit Dashboard (Analytics)

```bash
streamlit run apps/web_streamlit.py
# Open browser to http://localhost:8501
```

---

## 💻 Usage Modes

### CLI Application

**Purpose**: Automated video processing, batch jobs, production deployments

```bash
python -m apps.cli --video input.mp4 --no-firebase
```

**Features**:
- Processes entire video file
- Saves detections to local storage
- Optional Firebase integration
- Detailed logging to files
- Watchlist comparison & flagging

**Output**:
- Detected vehicle images in `outputs/detected_cars/`
- License plate crops in `outputs/detected_plates/`
- Processing logs in `logs/`
- Firebase data (if enabled)

---

### Demo Script

**Purpose**: Quick testing, visualization, presentations

```bash
python apps/demo.py --input video.mp4 --output demo_results/
```

**Features**:
- Processes images or videos
- Draws bounding boxes and labels
- Saves annotated frames
- Generates statistics report

**Output**:
```
demo_results/
├── annotated_frame_0040.jpg
├── annotated_frame_0080.jpg
├── detection_summary.txt
└── ...
```

---

### Gradio Web Interface

**Purpose**: Interactive usage, demonstrations, non-technical users

```bash
python apps/web_gradio.py
```

**Features**:
- Drag-and-drop video upload
- Real-time processing feedback
- Results table with all detections
- Traffic analysis statistics
- Flagged vehicle alerts

**UI Preview**:
- Video upload area
- Processing button
- Results summary (frames processed, vehicles tracked, etc.)
- Detection table (License plate, type, color, flagged status)

---

### Streamlit Dashboard

**Purpose**: Data analytics, monitoring, reporting

```bash
streamlit run apps/web_streamlit.py
```

**Features**:
- Modern dashboard UI
- Progress tracking
- Interactive charts
- Downloadable CSV results
- Vehicle analytics breakdown

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```bash
# Firebase Configuration (Optional)
FIREBASE_CREDENTIALS_PATH=config/firebase-credentials.json
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
FIREBASE_STORAGE_BUCKET=your-project.appspot.com

# Processing Settings
FRAME_SKIP=40          # Process every Nth frame (higher = faster but less accurate)
VIDEO_PATH=f1.mp4      # Default video for CLI

# Model Paths (Optional, defaults to anpr/models/weights/)
YOLO_MODEL_PATH=anpr/models/weights/yolov8n.pt
LICENSE_PLATE_MODEL_PATH=anpr/models/weights/run46.pt
```

### Configuration Class (`anpr/utils/config.py`)

All settings are centralized in the `Config` class:

```python
from anpr.utils.config import Config

# Access configuration
print(Config.FRAME_SKIP)
print(Config.VEHICLE_CLASS_IDS)
print(Config.MODEL_DIR)

# Ensure output directories exist
Config.ensure_directories()
```

---

## 🔍 How It Works

### Detection Pipeline

```
Input Video
    ↓
[Frame Extraction] (every FRAME_SKIP frames)
    ↓
[Vehicle Detection] ← YOLOv8 (COCO)
    ↓
[Object Tracking] ← SORT algorithm
    ↓
[License Plate Detection] ← Custom YOLO model
    ↓
[Plate-to-Vehicle Assignment] ← Spatial overlap check
    ↓
[OCR Text Recognition] ← EasyOCR
    ↓
[Format Validation] ← Pattern matching (AB12CDE)
    ↓
[Vehicle Classification] ← Type & Color models
    ↓
[Save & Upload] → Local storage + Firebase
    ↓
[Watchlist Check] ← Compare with flagged plates
    ↓
Output: Detections + Metadata
```

### Key Components

1. **ANPRDetector** (`anpr/core/detector.py`)
   - Unified interface for all detection operations
   - Manages vehicle detection, plate recognition, classification
   - Handles image preprocessing and postprocessing

2. **OCREngine** (`anpr/core/ocr.py`)
   - EasyOCR integration for text recognition
   - Character mapping for OCR error correction
   - License plate format validation (2 letters + 2 digits + 3 letters)

3. **ModelManager** (`anpr/models/manager.py`)
   - Singleton pattern for model loading
   - Lazy loading and caching
   - MD5 hash versioning for model tracking

4. **SORT Tracker** (`anpr/tracking/sort.py`)
   - Multi-object tracking across frames
   - Kalman filtering for smooth predictions
   - Hungarian algorithm for association

5. **FirebaseManager** (`anpr/integrations/firebase.py`)
   - Firebase Admin SDK integration
   - Storage upload for images
   - Realtime Database for metadata
   - Watchlist monitoring

---

## 🤖 Model Information

### Vehicle Detection Model

- **File**: `yolov8n.pt`
- **Type**: YOLOv8 Nano
- **Dataset**: COCO (pretrained)
- **Classes Detected**: car, motorcycle, bus, truck
- **Input Size**: 640x640
- **Performance**: ~45 FPS on GPU

### License Plate Detection Model

- **File**: `run46.pt`
- **Type**: YOLOv8 (custom trained)
- **Dataset**: Custom license plate dataset
- **Purpose**: Detect license plate bounding boxes
- **Input Size**: 640x640

### Vehicle Type Classifier

- **File**: `car.pt`
- **Type**: YOLOv8 Classification
- **Classes**: 6 types
  - Convertible, Coupe, Hatchback, Pickup, SUV, Sedan
- **Output**: Class prediction + confidence score

### Vehicle Color Classifier

- **File**: `color.pt`
- **Type**: YOLOv8 Classification
- **Classes**: 15 colors
  - beige, black, blue, brown, gold, green, grey, orange, pink, purple, red, silver, tan, white, yellow
- **Output**: Color prediction + confidence score

---

## ☁️ Firebase Integration

### Setup

1. Create Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
2. Enable Realtime Database and Storage
3. Generate service account credentials JSON
4. Place credentials at `config/firebase-credentials.json`
5. Update `.env` with your project details

### Database Structure

```
firebase-root/
├── users_detected/              # All detected vehicles
│   ├── {uid}/
│   │   ├── license_plate: "AB12CDE"
│   │   ├── timestamp: "2024-01-15 10:30:00"
│   │   ├── confidence: 0.95
│   │   ├── type: "Sedan"
│   │   ├── color: "black"
│   │   └── ...
│
├── users_database/              # Watchlist database
│   ├── {id}/
│   │   ├── License_Plate: "XY99ZZZ"
│   │   ├── Owner_Name: "..."
│   │   └── ...
│
├── flagged/                     # Matched flagged vehicles
│   └── {uid}: {...}
│
└── flagged_details/             # Full watchlist info for flags
    └── "XY99ZZZ": {...}
```

### Storage Structure

```
storage-bucket/
├── detected_cars/
│   └── car_AB12CDE_black_Sedan_2024-01-15T10:30:00_1234567890.jpg
│
└── detected_plates/
    └── plate_AB12CDE_2024-01-15T10:30:00_1234567890.jpg
```

---

## 🧪 Development

### Running Tests

```bash
# Run all tests
python tests/run_tests.py

# Run specific test file
pytest tests/test_detector.py -v

# Run with coverage
pytest --cov=anpr tests/
```

### Project Installation (Editable Mode)

```bash
pip install -e .
```

This allows you to modify code and test without reinstalling.

### Adding New Features

1. **New Detection Logic**: Extend `ANPRDetector` in `anpr/core/detector.py`
2. **New Classification Model**: Add to `ModelManager` in `anpr/models/manager.py`
3. **New Integration**: Create module in `anpr/integrations/`
4. **New UI**: Add app script in `apps/`

### Code Style

- Follow PEP8 conventions
- Use type hints for function signatures
- Add docstrings for all public functions/classes
- Keep functions focused and single-purpose

---

## 🐛 Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| **Model files not found** | Ensure `.pt` files are in `anpr/models/weights/` directory |
| **EasyOCR initialization fails** | Install with `pip install easyocr --upgrade` |
| **CUDA out of memory** | Reduce batch size or use CPU mode (`gpu=False` in OCREngine) |
| **Firebase connection fails** | Verify credentials path and internet connectivity |
| **Video file not opening** | Check video codec support, try converting to MP4 (H.264) |
| **Slow processing** | Increase `FRAME_SKIP` value in `.env` (e.g., 40 → 60) |
| **No license plates detected** | Check video quality and lighting conditions |
| **Import errors** | Ensure virtual environment is activated and dependencies installed |

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or modify `anpr/utils/logger.py` to set log level.

### Performance Optimization

1. **Increase FRAME_SKIP**: Process fewer frames (e.g., every 60th frame)
2. **Use GPU**: Ensure CUDA is installed for YOLOv8
3. **Reduce Video Resolution**: Preprocess video to 720p
4. **Disable Classification**: Set `enable_classification=False` in ANPRDetector
5. **Batch Processing**: Process multiple videos sequentially

---

## 📊 Example Output

### CLI Output

```
2024-12-24 10:30:15 - INFO - Starting ANPR Detection System...
2024-12-24 10:30:16 - INFO - Firebase initialized successfully
2024-12-24 10:30:18 - INFO - ANPR Detector initialized successfully
2024-12-24 10:30:20 - INFO - Processing video: f1.mp4 (1200 frames)
2024-12-24 10:30:25 - INFO - Processing frame 40/1200
2024-12-24 10:30:26 - INFO - Detected: AB12CDE (conf: 0.95)
2024-12-24 10:30:30 - INFO - Processing frame 80/1200
...
2024-12-24 10:35:00 - INFO - Video processing completed. Processed 1200 frames.
2024-12-24 10:35:01 - INFO - Checking for flagged vehicles...
2024-12-24 10:35:02 - WARNING - ALERT: 2 flagged vehicles detected!
2024-12-24 10:35:02 - WARNING -   - XY99ZZZ
2024-12-24 10:35:02 - INFO - ANPR Detection System completed successfully
```

### Demo Output

```
=== ANPR Demo Results ===
Frames processed: 30
Vehicles detected: 45
License plates detected: 28
License plates recognized: 22
Processing time: 12.5 seconds
FPS: 2.4

Detections saved to: demo_results/
- annotated_frame_0040.jpg
- annotated_frame_0080.jpg
- detection_summary.txt
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📧 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/Cambodia-ANPR-System/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/Cambodia-ANPR-System/discussions)
- **Email**: support@example.com

---

## 🎯 Roadmap

- [ ] Real-time webcam processing
- [ ] Multi-country license plate formats
- [ ] REST API server
- [ ] Docker containerization
- [ ] Model fine-tuning scripts
- [ ] Vehicle make/model recognition
- [ ] Advanced analytics dashboard
- [ ] Mobile app integration

---

**Built with ❤️ by the Cambodia ANPR Team**
