import asyncio
import cv2
import numpy as np
import time
import json
import requests
from datetime import datetime

# Simulated URLs
esp32_url = 'http://192.168.1.150'

# Create a QR code detector
detector = cv2.QRCodeDetector()

# Async function to send data to ESP32 or backend
async def send_success_to_esp32():
    try:
        response = await asyncio.to_thread(requests.get, esp32_url + '/display-success')
        if response.status_code == 200:
            print("Success message displayed on ESP32.")
        else:
            print("Failed to send success message to ESP32.")
    except Exception as e:
        print(f"Error: {e}")

# Process the QR code data
async def handle_qr_data(data):
    try:
        json_data = json.loads(data)
        print(f"Parsed JSON: {json_data}")
        
        # Simulate sending success to ESP32
        await send_success_to_esp32()
    except json.JSONDecodeError:
        print("Error: QR code data is not valid JSON.")

# Main function for QR code detection
async def detect_qr_code():
    cap = cv2.VideoCapture(0)  # Initialize webcam
    frame_counter = 0
    prev_data = ""

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        frame_counter += 1
        if frame_counter % 5 == 0:  # Process every 5th frame
            data, bbox, _ = detector.detectAndDecode(frame)
            if data and data != prev_data:  # If QR code detected and new data
                print(f"QR Code Data: {data}")
                await handle_qr_data(data)
                prev_data = data  # Update previous data

            cv2.putText(frame, "SCANNED SUCCESSFULLY", (50, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 3)

        cv2.imshow("Live Transmission", frame)

        key = cv2.waitKey(1)
        if key == 27:  # Exit on pressing ESC
            break

    cap.release()
    cv2.destroyAllWindows()

# Run the async main function
if __name__ == "__main__":
    asyncio.run(detect_qr_code())
