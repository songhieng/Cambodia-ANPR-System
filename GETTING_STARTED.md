# 🚀 Quick Start Guide

## Your ANPR System Has Been Refactored!

The project is now organized as a professional Python package. Here's how to get started:

---

## 📦 Step 1: Install Dependencies

```bash
# Activate virtual environment (if not already active)
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install all required packages
pip install -r requirements.txt
```

**Required packages**:
- `ultralytics` (YOLOv8)
- `easyocr` (License plate text recognition)
- `opencv-python` (Image processing)
- `gradio` & `streamlit` (Web interfaces)
- `firebase-admin` (Optional cloud integration)

---

## 🤖 Step 2: Download Model Weights

You need to place model files in `anpr/models/weights/`:

```
anpr/models/weights/
├── yolov8n.pt        # Vehicle detection
├── run46.pt          # License plate detection
├── car.pt            # Vehicle type classifier
├── color.pt          # Vehicle color classifier
└── make.pt           # Vehicle make classifier
```

**Download YOLOv8n**:
```bash
# Download official YOLOv8 nano model
curl -L https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -o anpr/models/weights/yolov8n.pt
```

The other models (run46.pt, car.pt, color.pt) are custom-trained - ensure they are in the weights folder.

---

## ⚙️ Step 3: Configure Environment

```bash
# Copy the environment template
cp config/.env.example .env

# Edit with your settings
notepad .env  # Windows
# nano .env  # Linux/Mac
```

**Minimum required** `.env` content:
```bash
# Processing settings
FRAME_SKIP=40
VIDEO_PATH=f1.mp4

# Firebase (optional - leave blank to skip)
FIREBASE_CREDENTIALS_PATH=
FIREBASE_DATABASE_URL=
FIREBASE_STORAGE_BUCKET=
```

---

## 🎯 Step 4: Choose Your Interface

### Option A: Command-Line (Recommended for Automation)

Process a video file:
```bash
python -m apps.cli --video path/to/video.mp4 --no-firebase
```

**Output**: Detections saved to `outputs/detected_cars/` and `outputs/detected_plates/`

---

### Option B: Demo Script (Best for Testing)

Quick test on an image or video:
```bash
python apps/demo.py --input test_image.jpg
```

**Output**: Annotated images saved to `outputs/demo_results/`

---

### Option C: Gradio Web UI (User-Friendly)

Launch interactive web interface:
```bash
python apps/web_gradio.py
```

Then open browser to: `http://localhost:7860`

**Features**:
- Drag-and-drop video upload
- Real-time processing
- Results table with all detections
- Automatic flagging of suspicious plates

---

### Option D: Streamlit Dashboard (Analytics)

Launch modern analytics dashboard:
```bash
streamlit run apps/web_streamlit.py
```

Then open browser to: `http://localhost:8501`

**Features**:
- Progress tracking
- Charts and visualizations
- Downloadable CSV results
- Vehicle type breakdown

---

## 🔍 Example Usage

### Process a video without Firebase:
```bash
python -m apps.cli --video my_traffic_video.mp4 --no-firebase
```

### Test on a single image:
```bash
python apps/demo.py --input car_photo.jpg --output results/
```

### Start web interface for team use:
```bash
python apps/web_gradio.py
```

---

## 📊 What to Expect

After processing, you'll find:

```
outputs/
├── detected_cars/
│   └── car_AB12CDE_black_Sedan_2024-12-24T10:30:00_1234567890.jpg
├── detected_plates/
│   └── plate_AB12CDE_2024-12-24T10:30:00_1234567890.jpg
└── demo_results/
    ├── annotated_frame_0040.jpg
    └── detection_summary.txt

logs/
└── anpr_20241224.log
```

---

## ⚠️ Troubleshooting

### "Module not found" errors
```bash
# Make sure you're in the project directory and venv is activated
cd Cambodia-ANPR-System
.\venv\Scripts\activate
pip install -r requirements.txt
```

### "Model file not found"
```bash
# Check that model files are in correct location
ls anpr/models/weights/*.pt
# Should show: yolov8n.pt, run46.pt, car.pt, color.pt, make.pt
```

### "Video file not opening"
- Ensure video is MP4 format (H.264 codec)
- Try with a different video file
- Check file path is correct

### Processing is slow
- Increase `FRAME_SKIP` in `.env` (e.g., from 40 to 60)
- Use GPU if available (CUDA)
- Reduce video resolution

---

## 🎓 Learn More

- **Full Documentation**: See [README.md](README.md)
- **Project Structure**: See [REFACTORING_COMPLETE.md](REFACTORING_COMPLETE.md)
- **Code Examples**: Check files in `apps/` directory

---

## 🆘 Need Help?

1. **Check logs**: `logs/anpr_YYYYMMDD.log` for detailed error messages
2. **Run tests**: `python tests/run_tests.py` to verify installation
3. **Read README**: Comprehensive guide with troubleshooting section

---

## ✅ Quick Verification

Test that everything works:

```bash
# 1. Check imports
python -c "print('Testing imports...'); from anpr.core import ANPRDetector; print('✓ Core imports OK')"

# 2. Check structure
python verify_structure.py

# 3. Run a quick demo
python apps/demo.py --input test.jpg
```

---

**You're all set! 🎉**

Start with the demo script or web interface to see the system in action!
