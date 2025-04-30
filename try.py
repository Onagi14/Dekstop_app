import cv2
import numpy as np

# IP address of the ESP32-CAM
ESP32_CAM_IP = "http:///stream"  # Replace <ESP32_IP> with the actual IP address of your ESP32-CAM

# OpenCV VideoCapture to stream the MJPEG video
cap = cv2.VideoCapture(ESP32_CAM_IP)

if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to grab frame")
        break

    # Display the resulting frame
    cv2.imshow("ESP32-CAM Stream", frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
