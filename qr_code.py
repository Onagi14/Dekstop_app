import asyncio
import cv2
import json
import requests
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from datetime import datetime  # Import datetime to get current date and time

# Simulated URLs
esp32_url = 'http://192.168.100.46'
backend_url = 'http://localhost:3002/api/attendance'  # Update with your Node.js backend URL

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
    global qr_data
    try:
        qr_data = json.loads(data)
        print(f"Parsed JSON: {qr_data}")

        # Get the current date and time in 12-hour format (Asia timezone assumed)
        current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")  # 12-hour time format with AM/PM
        
        # Add the current date and time to the QR data
        qr_data['scanned_at'] = current_time

        # Format the data for display
        formatted_data = (
            f"VALID DATA SCANNED\n\n\n\n\n"
            f"Event: {qr_data.get('event_name', 'N/A')}\n\n"
            f"Date & Time: {current_time}\n\n"  # Display the current date and time
            f"Email: {qr_data.get('email', 'N/A')}\n\n"
            f"Student ID: {qr_data.get('studentID', 'N/A')}\n\n"
            f"Year: {qr_data.get('year', 'N/A')}\n\n"
            f"Section: {qr_data.get('section', 'N/A')}\n\n"
        )
        
        # Update the label with the formatted data
        qr_label.config(text=formatted_data, fg="green")

        # Update the "Scanned Successfully" message
        scanned_label.config(text="Scanned Successfully!", fg="green")

        # Simulate sending success to ESP32
        await send_success_to_esp32()

        # Hide the success message after 3 seconds
        window.after(3000, lambda: scanned_label.config(text=""))

    except json.JSONDecodeError:
        print("Error: QR code data is not valid JSON.")
        qr_label.config(text="Error: Invalid QR code data.", fg="red")


# Function to update the frame in the Tkinter window
def update_frame():
    global prev_data, cap, detector, qr_label, record_button

    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame.")
        return

    # Process the frame for QR code detection
    data, bbox, _ = detector.detectAndDecode(frame)
    
    # Ensure that a valid QR code is detected
    if data and bbox is not None and len(bbox) > 0:
        if data != prev_data:
            print(f"QR Code Data: {data}")
            prev_data = data  # Update previous data
            
            # Run the async function to handle QR code data
            asyncio.run(handle_qr_data(data))

            # Enable the "Record attendance" button
            record_button.config(state=tk.NORMAL)
    else:
        # Handle case where QR code is not detected
        print("No QR code detected or invalid QR code.")
    
    # Display the result on the Tkinter window
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert to RGB format
    img = Image.fromarray(frame)  # Convert frame to Image object
    img_tk = ImageTk.PhotoImage(image=img)  # Convert Image object to Tkinter PhotoImage
    
    panel.configure(image=img_tk)  # Update the image on the Tkinter label
    panel.image = img_tk  # Keep a reference to avoid garbage collection

    window.after(1, update_frame)  # Call this function again immediately (for faster detection)
# Call this function again immediately (for faster detection)

# Function to record attendance (button handler)
def record_attendance():
    global qr_data
    if qr_data:
        # Send the attendance data to the backend API
        try:
            response = requests.post(backend_url, json=qr_data)
            if response.status_code == 201:
                messagebox.showinfo("Attendance Recorded", "Attendance has been successfully recorded.")
            else:
                messagebox.showerror("Error", "Failed to record attendance.")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"An error occurred while saving attendance: {e}")
        
        record_button.config(state=tk.DISABLED)  # Disable the button after clicking
    else:
        messagebox.showerror("Error", "No QR code data available to record.")

# Create the main window using Tkinter
window = tk.Tk()
window.title("QR Code Scanner")
window.geometry("900x600")  # Set the window size
window.configure(bg="#e6e6e6")

# Create a frame to split the window into two sections
frame = tk.Frame(window, bg="#e6e6e6")
frame.pack(fill=tk.BOTH, expand=True)

# Create a left frame for the camera feed
left_frame = tk.Frame(frame, width=450, height=600, bg="#dfe6e9", relief=tk.RAISED, bd=2)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
scanned_label = tk.Label(
    left_frame,
    text="",
    font=("Arial", 16, "bold"),
    bg="#dfe6e9",
    fg="green",
    anchor="center",
    pady=10,
)
scanned_label.pack(fill=tk.X, pady=(10, 0))

# Create a right frame for the QR code data and button
right_frame = tk.Frame(frame, width=450, height=600, bg="#ffffff", relief=tk.RAISED, bd=2)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# Initialize the webcam capture
cap = cv2.VideoCapture(0)  # 0 is typically the default webcam

# Set up the label to display the webcam feed
panel = tk.Label(left_frame, bg="#dfe6e9")
panel.pack(fill=tk.BOTH, expand=True)

# Label to show scanned QR code data
qr_label = tk.Label(
    right_frame,
    text="Scanned QR Data: None",
    font=("Arial", 14),
    justify="left",
    anchor="w",  # Align text to the left
    bg="#ffffff",
    fg="#34495e",
    relief=tk.GROOVE,
    wraplength=400,
    padx=10,
    pady=10,
)
qr_label.pack(padx=20, pady=(30, 10), fill=tk.BOTH, expand=True)

# Add a frame to contain the button at the bottom
button_frame = tk.Frame(right_frame, bg="#ffffff")
button_frame.pack(fill=tk.X, pady=10)

# Button to record attendance (appears after QR code scan)
record_button = tk.Button(
    button_frame,
    text="Record Attendance",
    font=("Arial", 14, "bold"),
    bg="#2ecc71",
    fg="white",
    relief=tk.RAISED,
    activebackground="#27ae60",
    activeforeground="white",
    command=record_attendance,
    state=tk.DISABLED,
    cursor="hand2",
)
record_button.pack(pady=10, padx=10, anchor="center")


prev_data = ""  # Store previous QR code data
qr_data = {}  # Store the current QR code data

# Start the frame update loop
update_frame()

# Run the Tkinter event loop
window.mainloop()

# Release the camera and clean up
cap.release()
cv2.destroyAllWindows()
