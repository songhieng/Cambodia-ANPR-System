# Cambodia ANPR (Automatic Number Plate Recognition) System

A professional vehicle detection and license plate recognition system using state-of-the-art deep learning models. This system leverages YOLO for object detection, EasyOCR for license plate reading, and integrates with Firebase for real-time data storage and retrieval.

## ✨ Features

- **Vehicle Detection**: Fast and accurate detection using YOLOv8
- **License Plate Recognition**: OCR-based plate reading with character mapping corrections
- **Vehicle Tracking**: SORT algorithm for consistent cross-frame tracking
- **Vehicle Classification**: Automatic type and color classification
- **Firebase Integration**: Real-time data storage and cloud-based image hosting
- **Web Interface**: Easy-to-use Gradio interface for video processing
- **Flagged Plates**: Automatic detection of suspicious/wanted vehicles
- **Professional Code Structure**: Modular, well-documented, and maintainable

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Modules](#modules)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)
- Firebase project with Realtime Database and Storage enabled

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/songhieng/Cambodia-ANPR-System.git
cd Cambodia-ANPR-System
```

2. **Create and activate virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure Firebase**
   - Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
   - Enable Realtime Database and Storage
   - Download your service account credentials JSON file
   - Copy `.env.example` to `.env` and update with your credentials

```bash
cp .env.example .env
# Edit .env with your Firebase credentials
```

## ⚙️ Configuration

The system uses environment variables for configuration. Create a `.env` file with:

```env
FIREBASE_CREDENTIALS_PATH=path/to/your/firebase-credentials.json
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VIDEO_PATH=./path/to/video.mp4  # Optional: default video path
```

### Configuration Options

Edit `config.py` to customize:
- Model paths
- Detection thresholds
- Frame skip rate
- Vehicle class mappings
- Output directories

## 📁 Project Structure

```
Cambodia-ANPR-System/
├── config.py                  # Configuration and settings
├── firebase_utils.py          # Firebase operations manager
├── detection_utils.py         # Detection and classification utilities
├── util.py                    # License plate OCR utilities
├── sort/                      # SORT tracking algorithm
│   ├── __init__.py
│   └── sort.py
├── main_refactored.py         # Main detection script
├── deploy_refactored.py       # Gradio web interface
├── type.py                    # Vehicle type classification utility
├── models/                    # YOLO model weights
│   └── run46.pt              # License plate detection model
├── detected_cars/             # Output: detected vehicle images
├── detected_plates/           # Output: detected plate images
├── DATA/                      # Output: flagged vehicle images
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## 💻 Usage

### Web Interface (Recommended)

Launch the Gradio web interface:

```bash
python deploy_refactored.py
```

Then open your browser to the provided URL and upload a video file.

### Command Line

Process a video from the command line:

```bash
python main_refactored.py
```

Set the video path in your `.env` file or modify the script.

### Vehicle Type Classification

Test vehicle type/make classification on a single image:

```bash
python type.py
```

## 📚 Modules

### `config.py`
Central configuration module containing:
- Model paths and settings
- Vehicle type/color mappings
- Output directory configuration
- Detection parameters

### `firebase_utils.py`
Firebase integration manager with:
- Singleton pattern for connection management
- Storage upload functionality
- Database read/write operations
- Error handling and logging

### `detection_utils.py`
Core detection utilities:
- `VehicleDetector`: Main detection class
- Vehicle and license plate detection
- Vehicle type and color classification
- Image saving and Firebase upload

### `util.py`
License plate processing utilities:
- OCR with EasyOCR
- Character mapping and correction
- License plate format validation
- Vehicle-plate association

### `sort/sort.py`
SORT (Simple Online and Realtime Tracking):
- Kalman filtering for prediction
- Hungarian algorithm for association
- Multi-object tracking across frames

## 🔒 Security

⚠️ **Important**: Never commit Firebase credentials or API keys to version control.

- All credentials should be stored in `.env` file
- `.env` is included in `.gitignore`
- Use `.env.example` as a template
- Rotate credentials if accidentally exposed

## 🛠️ Development

### Code Style

This project follows:
- PEP 8 style guidelines
- Type hints for function parameters
- Comprehensive docstrings
- Logging instead of print statements

### Adding New Features

1. Create feature branch
2. Implement changes with proper documentation
3. Add error handling and logging
4. Test thoroughly
5. Submit pull request

## 📊 Results

The system generates:
- **Detected Vehicle Images**: Saved in `detected_cars/`
- **License Plate Images**: Saved in `detected_plates/`
- **Flagged Vehicles**: Saved in `DATA/` directory
- **Firebase Database**: Real-time detection metadata
- **Processing Statistics**: Vehicle counts and traffic scores

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- YOLO by Ultralytics
- SORT algorithm by Alex Bewley
- EasyOCR for OCR functionality
- Firebase for cloud services

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact: [Repository Owner]

---

**Note**: This is a refactored and professionally structured version of the original Cambodia ANPR System, with improved code organization, documentation, and security practices.
