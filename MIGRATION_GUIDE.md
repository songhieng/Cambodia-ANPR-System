# 📋 Migration Checklist

## For Users Upgrading from Old Structure

If you were using the old flat structure, follow this checklist to migrate:

---

## ✅ Step 1: Backup Your Data

Before updating, backup important files:

```bash
# Backup outputs
cp -r detected_cars detected_cars_backup
cp -r detected_plates detected_plates_backup

# Backup any custom configuration
cp .env .env.backup 2>/dev/null || true
cp firebase-credentials.json firebase-credentials.json.backup 2>/dev/null || true
```

---

## ✅ Step 2: Update Import Statements

If you have custom scripts using the old code:

### Old imports:
```python
from config import Config
from util import read_license_plate, get_car
from detection_utils import VehicleDetector
from firebase_utils import FirebaseManager
from model_manager import get_model_manager
from logger_config import setup_logger
```

### New imports:
```python
from anpr.utils.config import Config
from anpr.core.ocr import OCREngine
from anpr.core.detector import ANPRDetector
from anpr.integrations.firebase import FirebaseManager
from anpr.models.manager import ModelManager
from anpr.utils.logger import setup_logger

# Usage changes:
ocr = OCREngine()
license_text, score = ocr.read_license_plate(image)
vehicle = ocr.get_vehicle_for_plate(plate, tracks)

# VehicleDetector is now ANPRDetector
detector = ANPRDetector(enable_classification=True)
```

---

## ✅ Step 3: Update Entry Points

### Old way:
```bash
python main.py
python deploy.py
python demo.py
streamlit run app_streamlit.py
```

### New way:
```bash
python -m apps.cli --video video.mp4
python apps/web_gradio.py
python apps/demo.py --input video.mp4
streamlit run apps/web_streamlit.py
```

---

## ✅ Step 4: Update Model Paths

### Old locations:
```
.
├── yolov8n.pt
├── car.pt
├── color.pt
├── make.pt
└── models/
    ├── run46.pt
    ├── train4.pt (removed)
    └── ...
```

### New location (all models together):
```
anpr/models/weights/
├── yolov8n.pt
├── run46.pt
├── car.pt
├── color.pt
└── make.pt
```

**Action**: Move all `.pt` files to `anpr/models/weights/`

```bash
# Windows
mkdir anpr\models\weights
move *.pt anpr\models\weights\
move models\run46.pt anpr\models\weights\

# Linux/Mac
mkdir -p anpr/models/weights
mv *.pt anpr/models/weights/
mv models/run46.pt anpr/models/weights/
```

---

## ✅ Step 5: Update Configuration

### Old: Mixed locations
- `.env` in root
- `firebase-credentials.json` in root
- Settings in `config.py`

### New: Centralized in `config/`
- `config/.env` (copy from root `.env`)
- `config/firebase-credentials.json` (copy from root)
- Settings accessed via `Config` class

**Action**:
```bash
# Create config directory if needed
mkdir config

# Copy environment file
cp .env config/.env 2>/dev/null || cp config/.env.example .env

# Move Firebase credentials
mv firebase-credentials.json config/ 2>/dev/null || true
```

---

## ✅ Step 6: Update Output Paths

### Old: Scattered output directories
```
.
├── detected_cars/
├── detected_plates/
├── demo_outputs/
└── DATA/
```

### New: Organized under `outputs/`
```
outputs/
├── detected_cars/
├── detected_plates/
├── demo_results/
└── flagged/
```

**Action**: Outputs will automatically go to new locations. Old outputs remain in place (safe to delete after verification).

---

## ✅ Step 7: Update Scripts/Automation

If you have scripts that call the ANPR system:

### Old script:
```bash
#!/bin/bash
python main.py
```

### New script:
```bash
#!/bin/bash
python -m apps.cli --video "$1" --no-firebase
```

### Old Python code:
```python
from detection_utils import VehicleDetector
from config import Config

detector = VehicleDetector(
    Config.YOLO_MODEL_PATH,
    Config.LICENSE_PLATE_MODEL_PATH,
    Config.CAR_TYPE_MODEL_PATH,
    Config.CAR_COLOR_MODEL_PATH
)

vehicles = detector.detect_vehicles(frame, Config.VEHICLE_CLASS_IDS)
```

### New Python code:
```python
from anpr.core.detector import ANPRDetector

detector = ANPRDetector(enable_classification=True)
vehicles = detector.detect_vehicles(frame)  # Uses Config.VEHICLE_CLASS_IDS by default
```

---

## ✅ Step 8: Clean Up Old Files

After verifying the new structure works:

```bash
# Remove old Python files from root (already cleaned in refactoring)
rm -f config.py model_manager.py logger_config.py
rm -f detection_utils.py firebase_utils.py util.py
rm -f main.py deploy.py app_streamlit.py demo.py

# Remove old directories
rm -rf models/ sort/ DATA/

# Optional: Remove old outputs after backing up
rm -rf detected_cars/ detected_plates/ demo_outputs/
```

---

## ✅ Step 9: Test Everything

Run comprehensive tests:

```bash
# 1. Verify structure
python verify_structure.py

# 2. Test imports (requires dependencies)
python -c "from anpr.core import ANPRDetector; print('✓ Imports OK')"

# 3. Run demo on a test image
python apps/demo.py --input test_image.jpg

# 4. Try CLI (without Firebase for quick test)
python -m apps.cli --video test_video.mp4 --no-firebase
```

---

## ✅ Step 10: Update Documentation

If you have internal documentation referencing the old structure:

- Update file paths
- Update import statements
- Update command examples
- Point to new [README.md](README.md) as source of truth

---

## 🔄 Quick Migration Script

Save this as `migrate.sh` (Linux/Mac) or `migrate.ps1` (Windows):

```bash
#!/bin/bash
# Quick migration script

echo "=== ANPR System Migration ==="

# 1. Backup
echo "Creating backups..."
cp -r detected_cars detected_cars_backup 2>/dev/null || true
cp -r detected_plates detected_plates_backup 2>/dev/null || true

# 2. Move models
echo "Moving model files..."
mkdir -p anpr/models/weights
mv *.pt anpr/models/weights/ 2>/dev/null || true
mv models/run46.pt anpr/models/weights/ 2>/dev/null || true

# 3. Setup config
echo "Setting up configuration..."
mkdir -p config
cp .env config/.env 2>/dev/null || cp config/.env.example .env
mv firebase-credentials.json config/ 2>/dev/null || true

# 4. Test
echo "Testing new structure..."
python verify_structure.py

echo "=== Migration complete! ==="
echo "Next: pip install -r requirements.txt"
```

---

## 📞 Need Help?

- **Documentation**: Read [README.md](README.md) and [GETTING_STARTED.md](GETTING_STARTED.md)
- **Issues**: Check [REFACTORING_COMPLETE.md](REFACTORING_COMPLETE.md) for breaking changes
- **Examples**: Look at files in `apps/` directory for usage patterns

---

## ✨ Benefits After Migration

Once migrated, you get:

- ✅ **Better organization**: Know exactly where everything is
- ✅ **Easier maintenance**: Update one component without affecting others
- ✅ **Multiple interfaces**: CLI, Gradio, Streamlit, Demo
- ✅ **Better logging**: Centralized with rotation
- ✅ **Importable package**: Use as library in other projects
- ✅ **Production-ready**: Proper error handling, config management

---

**Migration Status Tracker:**

- [ ] Backed up old outputs
- [ ] Updated import statements in custom scripts
- [ ] Moved model files to `anpr/models/weights/`
- [ ] Configured `.env` in `config/`
- [ ] Moved Firebase credentials to `config/`
- [ ] Updated automation scripts
- [ ] Tested new structure
- [ ] Cleaned up old files
- [ ] Updated internal documentation

**Once all checked, you're ready to go! 🚀**
