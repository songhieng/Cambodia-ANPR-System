from ultralytics import YOLO
import cv2
import numpy as np
from scipy.spatial import KDTree
import os
import datetime
from sort.sort import *
import util
import io
from util import get_car, read_license_plate
import firebase_admin
from firebase_admin import credentials, db, storage
import base64
import gradio as gr 

# Firebase Information Server
cred = credentials.Certificate("anpr-v3-b5bb8-firebase-adminsdk-8pkgt-d88b8f69b1.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://anpr-v3-b5bb8-default-rtdb.asia-southeast1.firebasedatabase.app',
    'storageBucket': 'anpr-v3-b5bb8.appspot.com'
})
ref = db.reference('/')



################################################################Need To Chaneg This Part too for the Demonastartion
users_ref = ref.child('right')

#Get Data from the RealTime Database of The Firebase 
root_ref = db.reference('/Detected')
# Fetch all data at the root of the database
Detected_data = root_ref.get()
plates = [data['plate'] for data in Detected_data.values()] if Detected_data else []
print(plates)

car_output_dir = "detected_cars"
plate_output_dir = "detected_plates"
Detected_dir = "DATA"

if not os.path.exists(car_output_dir):
    os.makedirs(car_output_dir)
if not os.path.exists(plate_output_dir):
    os.makedirs(plate_output_dir)
    
results = {}
mot_tracker = Sort()

# Load models
coco_model = YOLO('yolov8n.pt')
license_plate_detector = YOLO('./models/run46.pt')
model = YOLO('car.pt')
model1 = YOLO("color.pt")
# Load video


vehicles = [2, 3, 4, 5, 6, 7]

frame_skip = 40

# Read frames
frame_nmr = -1
ret = True

# Color Recognition functions
# Predefined colors dictionary
class_map_color = {
0: 'beige',
1: 'black',
2: 'blue',
3: 'brown',
4: 'gold',
5: 'green',
6: 'grey',
7: 'orange',
8: 'pink', 
9: 'purple',
10: 'red',
11: 'sivler',
12: 'tan',
13: 'white',
14: 'yellow'
}

# def reset_counts():
#     global vehicle_counts, current_frame_count, unique_vehicle_ids
#     vehicle_counts = {v: 0 for v in coco_class_to_vehicle_type.values()}  # Reset vehicle counts
#     unique_vehicle_ids.clear()  # Clear the set of unique vehicle IDs
#     current_frame_count = 0  # Reset frame counter

# def upload_text(path, text):
#     ref = db.reference(path)
#     ref.set(text)

# def upload_two_texts_append(path, text1, text2):
#     # Create a reference to the specified path in the Firebase Realtime Database
#     ref = db.reference(path)
    
#     # Structure the data as a dictionary with two keys, each holding one of the text strings
#     data = {
#         'text1': text1,
#         'text2': text2
#     }
    
#     # Use the push() method to add the data under a new, unique child node at the specified path
#     new_ref = ref.push(data)
    
#     print(f"Appended text1 and text2 under {path} at {new_ref.key}")

def upload_to_firebase(filename, destination_blob_name):
    bucket = storage.bucket()
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(filename)

    print(f"File {filename} uploaded to {destination_blob_name}.")

    # Return the public URL of the uploaded image
    return blob.public_url

    # print(f"Data saved to database with key: {new_user.key}")

def find_plate(search_plate, plate_array):
    return search_plate in plate_array

#----------------------------------------------------------------
#Car coutner




#================================================================
class_map = {0: 'Convertible', 1: 'Coupe', 2: 'Hatchback', 3: 'Pickup', 4: 'SUV', 5: 'Sedan'}

def process_video(video_path):
    cap = cv2.VideoCapture(video_path)
    # Initialize a set to keep track of unique vehicle IDs detected by SORT
    coco_class_to_vehicle_type = {
        2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus', 6: 'train', 7: 'truck'
    }
    vehicle_counts = {v: 0 for v in coco_class_to_vehicle_type.values()}
    # Initialize a set to keep track of unique vehicle IDs detected by SORT
    unique_vehicle_ids = set()
    # Initialize dictionary to map vehicle track IDs to their COCO class IDs
    track_id_to_class_id = {}
    cnt = 0
    score = 1
    frame_rate = cap.get(cv2.CAP_PROP_FPS)  # Get the frame rate of the video
    count_duration_seconds = 10  # Duration in seconds before resetting counts
    frame_count_for_reset = int(frame_rate * count_duration_seconds)  # Calculate number of frames for the duration
    current_frame_count = 0  # Initialize a counter for frames

    output_messages = []
    ret = True
    frame_nmr = 0
    while ret:
        frame_nmr += 1
        ret, frame = cap.read()
        current_frame_count += 1  # Increment frame counter
        
        if ret and frame_nmr % frame_skip == 0:
            # Perform detection
            detections = coco_model(frame)[0]
            detections_ = []
            
            for detection in detections.boxes.data.tolist():
                x1, y1, x2, y2, score, class_id = detection
                cnt+=1
                if int(class_id) in vehicles:
                    # Append detections with class ID for later reference
                    detections_.append([x1, y1, x2, y2, score, class_id])

            # Convert detections for tracking (excluding class_id)
            tracking_data = np.array([d[:5] for d in detections_])
            track_bbs_ids = mot_tracker.update(tracking_data)
            
            # Update track ID to class ID mapping
            for track in track_bbs_ids:
                track_id = int(track[4])
                # Find matching detection (assuming first match is correct for simplicity)
                for d in detections_:
                    if all([np.isclose(track[i], d[i], atol=1e-3) for i in range(4)]):  # Simple bounding box match
                        class_id = d[5]
                        track_id_to_class_id[track_id] = class_id
                        break

            # Debug print
            # if detections_:
            #     print(f"Vehicle detections with confidence: {[(d[4], 'Confidence') for d in detections_]}")

            # Track vehicles
            track_ids = mot_tracker.update(np.asarray(detections_))
            for track in track_bbs_ids:
                track_id = int(track[4])  # Track ID is the last element in the track array
                unique_vehicle_ids.add(track_id)

            # Debug print
            # if len(track_ids) > 0:
            #     print(f"Tracking IDs: {track_ids}")

            # Detect license plates
            license_plates = license_plate_detector(frame)[0]
            
            # Debug print
            # if license_plates:
            #     print(f"License plates detected: {len(license_plates.boxes.data.tolist())}")

            for license_plate in license_plates.boxes.data.tolist():
                x1, y1, x2, y2, score, class_id = license_plate
                
                # Assign license plate to car
                xcar1, ycar1, xcar2, ycar2, car_id = get_car(license_plate, track_ids)
                
                if car_id != -1:
                    print(f"Car ID: {car_id}, Confidence: {score}")  # Debug print
                    # upload_text('/', car_id)
                    # Crop and process license plate
                    license_plate_crop = frame[int(y1):int(y2), int(x1): int(x2), :]
                    license_plate_crop_gray = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY)
                    _, license_plate_crop_thresh = cv2.threshold(license_plate_crop_gray, 64, 255, cv2.THRESH_BINARY_INV)
        
                    # Read license plate number
                    license_plate_text, license_plate_text_score = read_license_plate(license_plate_crop_thresh)
                    


                    if license_plate_text is not None:
                        print(f"License Plate Text: {license_plate_text}")  # Debug print

                        is_plate_found = find_plate(license_plate_text, plates)
                        print(f"Is the plate '{license_plate_text}' found? {'Yes' if is_plate_found else 'No'}")
                        # if(is_plate_found):
                        #     print(1)
                        # else: 
                        #     continue

                        # Save the image of the detected car
                        car_image = frame[int(ycar1):int(ycar2), int(xcar1): int(xcar2), :]
                        
                        # dominant_color = find_dominant_color(car_image)
                        # closest_color_name = find_closest_color_name(dominant_color)
                        # print(f"Vehicle Color: {closest_color_name}")  # Debug print
                        results1 = model1(car_image)
        
                        # Assuming the top prediction is what you're interested in
                        top_prediction_index = results1[0].probs.top5[0]  # Index of the highest probability class
                        top_prediction_prob = results1[0].probs.top5conf[0].item()  # Highest probability

                        # Get the car type from the class_map
                        car_color = class_map_color[top_prediction_index]
                        print(f"{car_color}")

                        # Save the car image to the local filesystem
                        # cv2.imwrite(car_image_filename, car_image)


                        ################################
                        #Type of Car Detectin
                            # Perform object detection
                        results = model(car_image)
                        
                        # Assuming the top prediction is what you're interested in
                        top_prediction_index = results[0].probs.top5[0]  # Index of the highest probability class
                        top_prediction_prob = results[0].probs.top5conf[0].item()  # Highest probability

                        # Get the car type from the class_map
                        car_type = class_map[top_prediction_index]
                        print(f"{car_type}")

                        now_str = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
                        # Current date and time as Unix timestamp in milliseconds
                        now_int = int(datetime.datetime.utcnow().timestamp() * 1000)


                        # Save the image of the detected car
                        car_image_filename = os.path.join(car_output_dir, f"car_{license_plate_text}.jpg")
                        cv2.imwrite(car_image_filename, car_image)
                        car_image_url = upload_to_firebase(car_image_filename, f"detected_cars/car_{license_plate_text}_{now_str}_{now_int}_{car_color}_{car_type}.jpg")
                        
                        if(is_plate_found):
                            Detected_dir1 = os.path.join(Detected_dir, f"car_{license_plate_text}.jpg")
                            cv2.imwrite(Detected_dir1, car_image)
                            car_image_url = upload_to_firebase(Detected_dir1, f"DATA/car_{license_plate_text}_{now_str}_{now_int}_{car_color}_{car_type}.jpg")
                        

                        # Save the image of the detected license plate
                        license_plate_image_filename = os.path.join(plate_output_dir, f"plate_{license_plate_text}.jpg")
                        cv2.imwrite(license_plate_image_filename, license_plate_crop)
                        license_plate_url = upload_to_firebase(license_plate_image_filename, f"detected_plates/plate_{license_plate_text}_{now_str}_{now_int}.jpg")


                        # print(f"License plate image uploaded: {license_plate_url}")  # Debug print
        # print(f"Current vehicle counts (before potential reset): {vehicle_counts}")

    # Count vehicles by type after processing all frames
    vehicle_counts = {v: 0 for v in coco_class_to_vehicle_type.values()}
    for class_id in track_id_to_class_id.values():
        vehicle_type = coco_class_to_vehicle_type.get(class_id, 'unknown')
        if vehicle_type in vehicle_counts:
            vehicle_counts[vehicle_type] += 1

    # Print counts
    for vehicle_type, count in vehicle_counts.items():
        if vehicle_counts.items() == 0:
            score += count * 1
        else:
            score += count* 4

        print(f"Total {vehicle_type}s detected: {count}")
        data = users_ref.push({'text1': vehicle_type,'text2': count})
        # upload_two_texts_append("/right", vehicle_type, count)

    print(cnt) 
    print('/traffic-score1', score)
    # print('/traffic-score2', score)

    #####First
    # score1 = ref.child('TrafficScore1')
    # score1.set(score)


    #####Second
    score2 = ref.child('TrafficScore1')
    score2.set(score)

    output_messages.append(f"Traffic-Score1: {score}")
    # output_messages.append(f"Traffic-Score2: {score}")
    output_messages.append(f"Total detections: {cnt}")  # Assuming cnt is your counter for detections
    
    return "\n".join(output_messages)  # Join all messages into a single string


iface = gr.Interface(fn=process_video, 
                     inputs=gr.Video(label="Upload Video"), 
                     outputs="text",
                     title="Vehicle and License Plate Detection",
                     description="Upload a video to detect vehicles and license plates.")

if __name__ == "__main__":
    iface.launch(share=True)    