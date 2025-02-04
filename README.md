# Vehicle Detection and License Plate Recognition System

This project implements a real-time vehicle detection and license plate recognition system. It leverages state-of-the-art deep learning models for object detection (YOLO) and optical character recognition (EasyOCR) for license plate reading. Additionally, it tracks vehicles using the SORT algorithm, classifies vehicle types and colors, and integrates with Firebase for real-time data storage and retrieval.

---

## Table of Contents

- [Features](#features)
- [Overview](#overview)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Detailed Components](#detailed-components)
  - [YOLO for Vehicle Detection](#yolo-for-vehicle-detection)
  - [EasyOCR for License Plate Recognition](#easyocr-for-license-plate-recognition)
  - [Vehicle Tracking and Classification](#vehicle-tracking-and-classification)
  - [Firebase Integration](#firebase-integration)
- [Results and Outputs](#results-and-outputs)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Vehicle Detection:**  
  Utilizes YOLO (You Only Look Once) for fast and accurate detection of vehicles and license plates in real-time or recorded videos.

- **License Plate Recognition:**  
  Integrates EasyOCR to extract and interpret text from detected license plates, including character mapping corrections (e.g., converting "O" to "0").

- **Vehicle Tracking:**  
  Implements the SORT algorithm to track vehicles across video frames, ensuring smooth detection even when vehicles are in motion.

- **Color and Type Classification:**  
  Uses a pre-trained model to predict vehicle colors and another YOLO-based classifier to determine the type of vehicle (e.g., sedan, SUV, truck).

- **Firebase Integration:**  
  Connects to Firebase for real-time storage of detection data and images, enabling remote monitoring and data retrieval.

- **Web Interface:**  
  Provides an easy-to-use Gradio web interface for processing videos and visualizing the detection results.

---

## Overview

The system operates by first detecting vehicles in each video frame using YOLO models. Once a vehicle is detected, the system applies the SORT algorithm to track the movement across frames. When a license plate is identified, the license plate area is extracted and passed to EasyOCR for text recognition. The recognized text is then post-processed to correct common misclassifications.

In addition to detection, the system classifies the vehicle’s type and color. All detected images and corresponding metadata (license plate number, vehicle type, color, timestamp) are stored in Firebase. This makes the system suitable for applications such as parking management, traffic monitoring, and automated toll collection.

---

## Installation

### Prerequisites

- **Python:** Version 3.8 or above is recommended.
- **Virtual Environment:** (Recommended) Use `venv` or `conda` for dependency isolation.
- **Firebase Account:** Set up a Firebase project for database and storage integration.

### Clone the Repository

```bash
git clone https://github.com/your-repo/vehicle-detection.git
cd vehicle-detection
```

### Install Dependencies

Ensure that you have all the required packages installed by running:

```bash
pip install -r requirements.txt
```

**Required Dependencies:**

- `ultralytics` (for YOLO object detection)
- `opencv-python`
- `numpy`
- `scipy`
- `firebase-admin`
- `easyocr`
- `gradio`

---

## Project Structure

```
vehicle-detection/
│── models/                     # Pre-trained YOLO models for vehicles and license plates
│── detected_cars/              # Directory for saving images of detected vehicles
│── detected_plates/            # Directory for saving images of detected license plates
│── data/                      # Additional datasets and metadata
│── utils/                     # Utility functions and scripts
│   ├── color_thresholding.py  # Functions for vehicle color extraction using HSV thresholds
│   ├── license_plate_ocr.py   # OCR functions leveraging EasyOCR for license plate reading
│── type.py                    # YOLO-based vehicle type classification script
│── main.py                    # Main script for vehicle detection and tracking
│── deploy.py                  # Deployment script using Gradio for the web interface
│── v3.py                      # Enhanced version with Firebase integration for vehicle tracking
│── requirements.txt           # List of required dependencies
│── README.md                  # This documentation file
```

---

## Usage

### Running Vehicle Detection

To execute the main detection script:

```bash
python main.py
```

This script initializes the YOLO models, starts vehicle detection and tracking, extracts license plate regions, and saves the corresponding images and data.

### Running the Web Interface

For an interactive web-based video processing interface, run:

```bash
python deploy.py
```

This will launch a Gradio interface where users can upload video files and view real-time detection results.

### Processing a Video File with Firebase Integration

To process a video file and integrate with Firebase for data storage, use:

```bash
python v3.py --input your_video.mp4
```

---

## Detailed Components

### YOLO for Vehicle Detection

**YOLO (You Only Look Once):**  
YOLO is a deep learning-based object detection system known for its speed and accuracy. In this project:

- **Detection Process:**  
  The YOLO model scans each video frame and outputs bounding boxes along with confidence scores for detected objects (vehicles and license plates).

- **Pre-trained Models:**  
  Pre-trained weights are provided in the `models/` directory. You can fine-tune these models further if needed.

- **Benefits:**  
  The one-stage detection mechanism of YOLO ensures that vehicle detection happens in real-time, which is crucial for live monitoring applications.

### EasyOCR for License Plate Recognition

**EasyOCR:**  
EasyOCR is a robust Optical Character Recognition (OCR) tool that supports multiple languages and works efficiently with license plate images.

- **OCR Process:**  
  Once a license plate is detected by the YOLO model, the region of interest is cropped and passed to EasyOCR. The recognized text is then filtered and corrected (e.g., mapping similar looking characters such as "O" and "0").

- **Character Mapping:**  
  The `license_plate_ocr.py` script includes routines for adjusting common OCR misinterpretations, ensuring the final license plate string is accurate.

### Vehicle Tracking and Classification

- **Tracking with SORT:**  
  The Simple Online and Realtime Tracking (SORT) algorithm is used to maintain consistent identification of vehicles across frames. This enhances detection stability and prevents duplicate records.

- **Color Classification:**  
  A dedicated model and the `color_thresholding.py` utility are used to determine the color of the detected vehicles based on HSV thresholds.

- **Vehicle Type Classification:**  
  The `type.py` script employs another YOLO model specifically trained to classify vehicle types (e.g., sedan, SUV, truck).

### Firebase Integration

Firebase is used to store detection metadata and images in real-time.

- **Setup:**  
  - Create a Firebase project on the [Firebase Console](https://console.firebase.google.com/).
  - Download the Service Account Key (a JSON file) and place it in your project directory.
  - Enable Firebase Realtime Database and Storage.

- **Configuration:**  
  Update the Firebase initialization section in `main.py`, `v3.py`, or `deploy.py` with your credentials:

  ```python
  import firebase_admin
  from firebase_admin import credentials

  cred = credentials.Certificate("your-firebase-adminsdk.json")
  firebase_admin.initialize_app(cred, {
      'databaseURL': 'https://your-firebase-project.firebaseio.com',
      'storageBucket': 'your-firebase-project.appspot.com'
  })
  ```

- **Data Handling:**  
  The system uploads the following data for each detection:
  - License Plate Number
  - Vehicle Type
  - Vehicle Color
  - Timestamp of detection
  - Associated images stored in Firebase Storage

---

## Results and Outputs

After processing, the system generates:

- **Detected Vehicle Images:**  
  Saved in the `detected_cars/` directory.

- **License Plate Images:**  
  Saved in the `detected_plates/` directory.

- **Firebase Database Entries:**  
  Each entry contains metadata similar to:

  ```json
  {
      "license_plate": "ABC1234",
      "vehicle_type": "SUV",
      "color": "Red",
      "timestamp": "2025-02-04T12:30:00"
  }
  ```

These outputs can be further used for analytics, reporting, or real-time monitoring dashboards.

---

## Contributing

Contributions to improve the system are welcome. Please follow these steps:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/new-feature`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature/new-feature`).
5. Create a new Pull Request.

---

## License

This project is licensed under the [MIT License](LICENSE).
