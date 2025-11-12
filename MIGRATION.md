# Migration Guide

This guide helps you migrate from the old codebase to the refactored version.

## Overview

The codebase has been refactored to improve:
- Code organization and modularity
- Security (credentials management)
- Documentation and maintainability
- Error handling and logging
- Type safety with type hints

## Breaking Changes

### 1. File Structure Changes

**Old Files → New Files**
- `deploy.py.py` → `deploy_refactored.py`
- `main.py` → `main_refactored.py`
- `new.py` → **REMOVED** (was empty)
- `uti.py` → **REMOVED** (was unused)
- `v3.py` → Functionality moved to `main_refactored.py` and `deploy_refactored.py`

### 2. Configuration Changes

**Before:**
```python
# Hardcoded in files
cred = credentials.Certificate("anpr-5a023-firebase-adminsdk-mrrmo-d159fa0e4d.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://anpr-5a023-default-rtdb.asia-southeast1.firebasedatabase.app',
    'storageBucket': 'anpr-5a023.appspot.com'
})
```

**After:**
```python
# Use environment variables
from dotenv import load_dotenv
load_dotenv()

from firebase_utils import get_firebase_manager

firebase_manager = get_firebase_manager()
firebase_manager.initialize(
    os.environ.get('FIREBASE_CREDENTIALS_PATH'),
    os.environ.get('FIREBASE_DATABASE_URL'),
    os.environ.get('FIREBASE_STORAGE_BUCKET')
)
```

### 3. Module Imports

**Before:**
```python
from sort.sort import *
from util import get_car, read_license_plate
```

**After:**
```python
from sort.sort import Sort
from util import get_car, read_license_plate
from config import Config
from firebase_utils import get_firebase_manager
from detection_utils import VehicleDetector
```

## Migration Steps

### Step 1: Update Environment Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your Firebase credentials in `.env`:
   ```env
   FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json
   FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
   FIREBASE_STORAGE_BUCKET=your-project.appspot.com
   ```

3. Move Firebase credential JSON files out of the repository (they should not be committed)

### Step 2: Update Dependencies

Install the updated requirements:
```bash
pip install -r requirements.txt
```

New dependencies added:
- `python-dotenv` - Environment variable management
- `gradio>=3.0.0` - Web interface (already used but now in requirements)

### Step 3: Update Your Code

#### If you're using `main.py`:

**Option A: Use the refactored version directly**
```bash
python main_refactored.py
```

**Option B: Update your code to use new modules**
```python
from config import Config
from firebase_utils import get_firebase_manager
from detection_utils import VehicleDetector

# Initialize detector
detector = VehicleDetector(
    Config.YOLO_MODEL_PATH,
    Config.LICENSE_PLATE_MODEL_PATH
)

# Initialize Firebase
firebase_manager = get_firebase_manager()
firebase_manager.initialize(...)
```

#### If you're using `deploy.py`:

Simply use the new version:
```bash
python deploy_refactored.py
```

#### If you're using `v3.py`:

The functionality has been merged into `deploy_refactored.py`. Use that instead:
```bash
python deploy_refactored.py
```

### Step 4: Update Configuration Values

Edit `config.py` to update:
- Model paths (if different from defaults)
- Frame skip rate
- Output directories
- Vehicle class mappings

### Step 5: Test Your Setup

1. Test with a sample video:
   ```bash
   python main_refactored.py
   ```

2. Test the web interface:
   ```bash
   python deploy_refactored.py
   ```

## Code Examples

### Example 1: Vehicle Detection

**Before:**
```python
coco_model = YOLO('yolov8n.pt')
license_plate_detector = YOLO('./models/run46.pt')

detections = coco_model(frame)[0]
# ... manual processing
```

**After:**
```python
from detection_utils import VehicleDetector
from config import Config

detector = VehicleDetector(
    Config.YOLO_MODEL_PATH,
    Config.LICENSE_PLATE_MODEL_PATH
)

detections = detector.detect_vehicles(frame, Config.VEHICLE_CLASS_IDS)
```

### Example 2: Firebase Upload

**Before:**
```python
bucket = storage.bucket()
blob = bucket.blob(destination_blob_name)
blob.upload_from_filename(filename)
```

**After:**
```python
from firebase_utils import get_firebase_manager

firebase_manager = get_firebase_manager()
url = firebase_manager.upload_to_storage(filename, destination_blob_name)
```

### Example 3: License Plate Processing

**Before:**
```python
license_plate_crop = frame[int(y1):int(y2), int(x1):int(x2), :]
license_plate_crop_gray = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY)
_, license_plate_crop_thresh = cv2.threshold(license_plate_crop_gray, 64, 255, cv2.THRESH_BINARY_INV)
license_plate_text, license_plate_text_score = read_license_plate(license_plate_crop_thresh)
```

**After:**
```python
license_plate_text, text_score, plate_image = detector.process_license_plate(
    frame,
    license_plate
)
```

## Benefits of Migration

### 1. Better Security
- Credentials no longer hardcoded
- Environment variables for sensitive data
- `.gitignore` prevents accidental commits

### 2. Improved Code Quality
- Type hints for better IDE support
- Comprehensive error handling
- Professional logging instead of print statements

### 3. Better Organization
- Modular design with clear separation of concerns
- Reusable utilities
- Centralized configuration

### 4. Easier Maintenance
- Well-documented code
- Consistent naming conventions
- Reduced code duplication

## Troubleshooting

### Issue: Module not found errors

**Solution:** Ensure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

### Issue: Firebase initialization fails

**Solution:** Check your `.env` file:
1. Ensure all required variables are set
2. Verify the credentials file path is correct
3. Check that Firebase database URL and storage bucket are correct

### Issue: Model files not found

**Solution:** Ensure model files are in the correct locations:
- `yolov8n.pt` in root directory
- `car.pt` in root directory
- `color.pt` in root directory
- `models/run46.pt` for license plate detection

### Issue: Permission errors with Firebase

**Solution:** 
1. Verify your Firebase service account has proper permissions
2. Check Firebase Realtime Database and Storage rules
3. Ensure the service account JSON file is valid

## Backward Compatibility

The old files (`main.py`, `v3.py`, `deploy.py`) are still present but not recommended for use. They contain:
- Hardcoded credentials (security risk)
- Duplicate code
- Less error handling
- No type hints

It's strongly recommended to migrate to the refactored versions.

## Support

If you encounter issues during migration:
1. Check this guide for common solutions
2. Review the new module documentation
3. Open an issue on GitHub with details

## Additional Resources

- [README.md](README.md) - Updated project documentation
- [config.py](config.py) - Configuration reference
- [firebase_utils.py](firebase_utils.py) - Firebase integration docs
- [detection_utils.py](detection_utils.py) - Detection utilities docs
