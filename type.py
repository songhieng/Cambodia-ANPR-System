from ultralytics import YOLO
import cv2

# Load the YOLO model
model = YOLO("make.pt")

# Define the mapping of class indices to car types
# class_map = {
# 0: 'beige',
# 1: 'black',
# 2: 'blue',
# 3: 'brown',
# 4: 'gold',
# 5: 'green',
# 6: 'grey',
# 7: 'orange',
# 8: 'pink', 
# 9: 'purple',
# 10: 'red',
# 11: 'sivler',
# 12: 'tan',
# 13: 'white',
# 14: 'yellow'
# }
# Open the video file
video_path = '2.jpg'
result = model(video_path)

# cap = cv2.VideoCapture(video_path)

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     # Perform object detection
#     results = model(frame)
    
#     # Assuming the top prediction is what you're interested in
#     top_prediction_index = results[0].probs.top5[0]  # Index of the highest probability class
#     top_prediction_prob = results[0].probs.top5conf[0].item()  # Highest probability

#     # Get the car type from the class_map
#     # car_type = class_map[top_prediction_index]
#     print('/n')
#     print(f"{class_map[top_prediction_index]}")

# cap.release()
# cv2.destroyAllWindows()