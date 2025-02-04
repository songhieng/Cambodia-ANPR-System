from ultralytics import YOLO
import cv2
import numpy as np
import util
from sort.sort import *
from util import get_car, read_license_plate
import os
import firebase_admin
from firebase_admin import storage
import datetime

current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


#Firebase Information Server 
import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate("anpr-5a023-firebase-adminsdk-mrrmo-d159fa0e4d.json")
firebase_admin.initialize_app(cred, { 
    'databaseURL': 'https://anpr-5a023-default-rtdb.asia-southeast1.firebasedatabase.app',
    'storageBucket': 'anpr-5a023.appspot.com'
})
ref = db.reference('/')
users_ref = ref.child('users_detected')
#Firebase Information Server


# Directories for saving detected cars and license plates
car_output_dir = "detected_cars"
plate_output_dir = "detected_plates"
if not os.path.exists(car_output_dir):
    os.makedirs(car_output_dir)
if not os.path.exists(plate_output_dir):
    os.makedirs(plate_output_dir)


results = {}
mot_tracker = Sort()

# Load models
coco_model = YOLO('yolov8n.pt')
license_plate_detector = YOLO('./models/run46.pt')

# Load video
cap = cv2.VideoCapture('./f1.mp4')

vehicles = [2, 3, 4, 5, 6, 7]

frame_skip = 40

# Read frames
frame_nmr = -1
ret = True




def upload_to_firebase(filename, destination_blob_name):
    """
    Uploads a file to Firebase Cloud Storage.
    
    Parameters:
    - filename: Path to the file to upload.
    - destination_blob_name: Storage object name.
    """

    bucket = storage.bucket()
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(filename)

    print(f"File {filename} uploaded to {destination_blob_name}.")

    # Return the public URL of the uploaded image
    return blob.public_url




while ret:
    frame_nmr += 1
    ret, frame = cap.read()
    if ret and frame_nmr % frame_skip == 0:
        print(f"Processing frame {frame_nmr}")  # Debug print
        results[frame_nmr] = {}
        
        # Detect vehicles
        detections = coco_model(frame)[0]
        detections_ = []
        
        for detection in detections.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = detection
            if int(class_id) in vehicles:
                detections_.append([x1, y1, x2, y2, score])
        
        # Debug print
        if detections_:
            print(f"Vehicle detections with confidence: {[(d[4], 'Confidence') for d in detections_]}")

        # Track vehicles
        track_ids = mot_tracker.update(np.asarray(detections_))
        
        # Debug print
        if len(track_ids) > 0:
            print(f"Tracking IDs: {track_ids}")

        # Detect license plates
        license_plates = license_plate_detector(frame)[0]
        
        # Debug print
        if license_plates:
            print(f"License plates detected: {len(license_plates.boxes.data.tolist())}")

        for license_plate in license_plates.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = license_plate
            
            # Assign license plate to car
            xcar1, ycar1, xcar2, ycar2, car_id = get_car(license_plate, track_ids)
            
            if car_id != -1:
                print(f"Car ID: {car_id}, Confidence: {score}")  # Debug print
                
                # Crop and process license plate
                license_plate_crop = frame[int(y1):int(y2), int(x1): int(x2), :]
                license_plate_crop_gray = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY)
                _, license_plate_crop_thresh = cv2.threshold(license_plate_crop_gray, 64, 255, cv2.THRESH_BINARY_INV)

                # Read license plate number
                license_plate_text, license_plate_text_score = read_license_plate(license_plate_crop_thresh)
                
                # # Resize the thresholded license plate for better visibility
                # scale_factor = 2  # Change this value as needed
                # h, w = license_plate_crop_thresh.shape[:2]
                # resized_license_plate = cv2.resize(license_plate_crop_thresh, (int(w * scale_factor), int(h * scale_factor)))
                
                # # Display the resized thresholded license plate
                # cv2.imshow('License Plate Thresholded', resized_license_plate)
                # key = cv2.waitKey(0)  # Wait until a key is pressed
                # if key == 27:  # ESC key
                #     break


                if license_plate_text is not None:
                    print(f"License Plate Text: {license_plate_text}")  # Debug print
                    
                    # Save the image of the detected car
                    car_image = frame[int(ycar1):int(ycar2), int(xcar1): int(xcar2), :]
                    car_image_filename = os.path.join(car_output_dir, f"car_{license_plate_text}.jpg")
                    cv2.imwrite(car_image_filename, car_image)
                    car_image_url = upload_to_firebase(car_image_filename, f"detected_cars/car_{license_plate_text}.jpg")

                    # Save the image of the detected license plate
                    license_plate_image_filename = os.path.join(plate_output_dir, f"plate_{license_plate_text}.jpg")
                    cv2.imwrite(license_plate_image_filename, license_plate_crop)
                    license_plate_url = upload_to_firebase(license_plate_image_filename, f"detected_plates/plate_{license_plate_text}.jpg")


                    new_user = users_ref.push({
                        'license_plate': license_plate_text,
                        'timestamp': current_time
                    })


                    results[frame_nmr][car_id] = {
                        'car': {'bbox': [xcar1, ycar1, xcar2, ycar2], 'score': score},
                        'license_plate': {'bbox': [x1, y1, x2, y2],
                                          'text': license_plate_text,
                                          'bbox_score': score,
                                          'text_score': license_plate_text_score}
                    }



# Fetch data from Firebase
users_detected_data = users_ref.get()
users_database_ref = ref.child('users_database')
users_database_data = users_database_ref.get()

# Extract license plate values
detected_license_plates = {uid: details['license_plate'] for uid, details in users_detected_data.items()}
database_license_plates = {uid: entry['License_Plate'] for uid, entry in enumerate(users_database_data) if 'License_Plate' in entry}


# Find matching license plates and store the complete data
flagged_data = {}

for uid, license_plate in detected_license_plates.items():
    if license_plate in database_license_plates.values():
        flagged_data[uid] = users_detected_data[uid]

# Write flagged data to Firebase if any matches found
if flagged_data:
    flagged_ref = ref.child('flagged')
    flagged_ref.set(flagged_data)

flagged_details_data = {}  # Dictionary to store detailed flagged data

# Collect details from users_database for flagged License_Plate and upload to Firebase
for uid in flagged_data:
    license_plate = flagged_data[uid]['license_plate']
    for user_id, user_data in enumerate(users_database_data):
        if user_data.get('License_Plate') == license_plate:
            print("\nFlagged User Details:")
            flagged_user_detail = {}  # Dictionary to store details of this flagged user
            for key, value in user_data.items():
                print(f"{key}: {value}")
                flagged_user_detail[key] = value
            flagged_details_data[user_id] = flagged_user_detail  # Append to main dictionary

# Push flagged user details to Firebase
if flagged_details_data:
    flagged_details_ref = ref.child('flagged_details')
    flagged_details_ref.set(flagged_details_data)

print("Suspected data")
print(flagged_data)


if flagged_data:
    flagged_ref = ref.child('flagged')
    flagged_ref.set(flagged_data)

# Collect details from users_database for flagged License_Plate and upload to Firebase
# ...
if flagged_details_data:
    flagged_details_ref = ref.child('flagged_details')
    flagged_details_ref.set(flagged_details_data)
