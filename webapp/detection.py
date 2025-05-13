import os
import cv2
import numpy as np
import tensorflow as tf
import traceback
from datetime import datetime
import platform

# Define paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
scripts_path = os.path.join(project_dir, 'scripts')
models_path = os.path.join(project_dir, 'models')
MODEL_PATH = os.path.join(models_path, 'resnet_anomaly_detection1.h5')

# Define folders for uploads and suspects
UPLOAD_FOLDER = os.path.join(project_dir, 'uploads')
SUSPECTS_FOLDER = os.path.join(project_dir, 'suspects')

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SUSPECTS_FOLDER, exist_ok=True)

# Load the model directly - no fallback allowed
model = None

print(f"Loading model from {MODEL_PATH}")
model = tf.keras.models.load_model(MODEL_PATH, compile=False)
print("✅ Model loaded successfully")

# Test the model with a dummy input
dummy_input = np.zeros((1, 64, 64, 3), dtype=np.float32)
_ = model.predict(dummy_input)
print("✅ Model prediction test successful")

# Function to preprocess images to the correct size
def preprocess_image(image_path, target_size=(64, 64)):
    """
    Preprocess image to match the model's expected input shape (64x64x3)
    """
    try:
        # Read image
        if isinstance(image_path, str):
            img = cv2.imread(image_path)
            if img is None:
                print(f"❌ Error: Could not read image at {image_path}")
                # Create a blank image as fallback
                img = np.zeros((64, 64, 3), dtype=np.uint8)
        else:
            # If image is already a numpy array
            img = image_path
            
        # Resize to target size (64x64 for our model)
        img = cv2.resize(img, target_size)
        
        # Convert BGR to RGB if needed
        if len(img.shape) == 3 and img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
        # Normalize pixel values to [0, 1]
        img = img.astype(np.float32) / 255.0
        
        return img
    except Exception as e:
        print(f"❌ Error preprocessing image: {e}")
        traceback.print_exc()
        # Return a blank image as fallback
        return np.zeros((64, 64, 3), dtype=np.float32)

def detect_crime(file_path):
    """
    Detect crime in an image or video file using only the real model
    """
    
    try:
        # For videos, extract multiple frames for better detection
        if file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
            cap = cv2.VideoCapture(file_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Sample multiple frames for more robust detection
            frame_indices = []
            if total_frames > 0:
                # Take frames from different parts of the video
                frame_indices = [int(total_frames * i / 5) for i in range(5)]
            
            frames = []
            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
            
            cap.release()
            
            if not frames:
                print(f"❌ Error: Could not read video frames from {file_path}")
                raise ValueError("Could not extract frames from video")
            
            # Process all frames and get predictions
            predictions = []
            for frame in frames:
                img = preprocess_image(frame)
                # Expand dimensions to create batch of size 1
                img_array = np.expand_dims(img, axis=0)
                
                # Get prediction for this frame
                pred = model.predict(img_array)
                predictions.append(pred[0])
            
            # Average predictions across frames
            avg_prediction = np.mean(predictions, axis=0)
            
            # Use the model's original predictions without any bias
            
            # Get the class with highest probability
            crime_class = int(np.argmax(avg_prediction))
            confidence = float(avg_prediction[crime_class])
            
            return crime_class, confidence
                
        else:
            # Process image directly
            img = preprocess_image(file_path)
            
            # Expand dimensions to create batch of size 1
            img_array = np.expand_dims(img, axis=0)
            
            # Get prediction
            predictions = model.predict(img_array)
            
            # Use the model's original predictions without any bias
            
            # Get the class with highest probability
            crime_class = int(np.argmax(predictions[0]))
            confidence = float(predictions[0][crime_class])
            
            return crime_class, confidence
        
    except Exception as e:
        print(f"❌ Error in crime detection: {e}")
        traceback.print_exc()
        # Re-raise the exception instead of using a fallback
        raise

def extract_suspect_faces(video_path):
    """Extract faces from video frames and save them"""
    try:
        # Check if file exists and is readable
        if not os.path.exists(video_path):
            print(f"❌ Video file not found: {video_path}")
            return []
            
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Could not open video file: {video_path}")
            return []
            
        # Load face cascade - try multiple paths
        haar_paths = [
            os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"),
            "haarcascade_frontalface_default.xml",
            os.path.join(current_dir, "haarcascade_frontalface_default.xml"),
            os.path.join(scripts_path, "haarcascade_frontalface_default.xml")
        ]
        
        face_cascade = None
        for haar_path in haar_paths:
            if os.path.exists(haar_path):
                face_cascade = cv2.CascadeClassifier(haar_path)
                if not face_cascade.empty():
                    print(f"✅ Loaded face cascade from: {haar_path}")
                    break
        
        if face_cascade is None or face_cascade.empty():
            print("❌ Failed to load face cascade classifier from any path")
            # Download cascade file as a last resort
            try:
                import urllib.request
                haar_path = os.path.join(current_dir, "haarcascade_frontalface_default.xml")
                urllib.request.urlretrieve(
                    "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml",
                    haar_path
                )
                face_cascade = cv2.CascadeClassifier(haar_path)
                if face_cascade.empty():
                    print("❌ Downloaded cascade file is invalid")
                    return []
                print("✅ Downloaded and loaded face cascade")
            except Exception as e:
                print(f"❌ Error downloading cascade file: {e}")
                return []

        suspect_faces = []
        frame_count = 0
        
        # Get total frames for better sampling
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            # If we can't get frame count, use a default
            sample_interval = 10
        else:
            # Sample up to 20 frames across the video
            sample_interval = max(1, total_frames // 20)
        
        # Generate a timestamp for unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            # Only process at intervals
            if frame_count % sample_interval != 0:
                continue
                
            # Convert to grayscale for face detection
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            except Exception as e:
                print(f"❌ Error converting frame to grayscale: {e}")
                continue
                
            # Detect faces
            try:
                faces = face_cascade.detectMultiScale(
                    gray, 
                    scaleFactor=1.1, 
                    minNeighbors=5,
                    minSize=(30, 30)  # Minimum face size
                )
            except Exception as e:
                print(f"❌ Error detecting faces: {e}")
                continue

            # Process detected faces
            for i, (x, y, w, h) in enumerate(faces):
                try:
                    # Ensure face region is within frame bounds
                    if x < 0 or y < 0 or x+w > frame.shape[1] or y+h > frame.shape[0]:
                        continue
                        
                    face = frame[y:y+h, x:x+w]
                    # Simple quality check - skip very small images or low contrast
                    if face.size == 0 or np.std(face) < 20:
                        continue
                    
                    # Create a unique filename for this face
                    face_filename = f"suspect_{timestamp}_{frame_count}_{i}.jpg"
                    face_path = os.path.join(SUSPECTS_FOLDER, face_filename)
                    
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(face_path), exist_ok=True)
                    
                    # Save the face image
                    cv2.imwrite(face_path, face)
                    suspect_faces.append(face_filename)
                    
                    # Limit to 10 faces max
                    if len(suspect_faces) >= 10:
                        cap.release()
                        return suspect_faces
                except Exception as e:
                    print(f"❌ Error saving face: {e}")
                    continue

        cap.release()
        return suspect_faces
    except Exception as e:
        print(f"❌ Error in extract_suspect_faces: {e}")
        traceback.print_exc()
        return []

def detect_weapon(video_path):
    """Detect weapons in video using OpenCV or YOLOv5 if available"""
    try:
        # Check if YOLOv5 is available
        yolo_available = False
        try:
            import torch
            yolo_available = True
        except ImportError:
            print("⚠️ torch not available, using simple weapon detection")
            
        if yolo_available:
            try:
                model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
                print("✅ Loaded YOLOv5 model for weapon detection")
            except Exception as e:
                print(f"❌ Failed to load YOLOv5: {e}")
                yolo_available = False
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Could not open video file: {video_path}")
            return False

        weapon_detected = False
        frame_count = 0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Process frames at intervals to improve performance
        frame_interval = max(1, total_frames // 10) if total_frames > 0 else 30

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            # Only process some frames for efficiency
            if frame_count % frame_interval != 0:
                continue
                
            if yolo_available:
                # Use YOLOv5 for detection
                results = model(frame)
                
                # Look for weapons in the detections
                for pred in results.xyxy[0].cpu().numpy():  
                    label_idx = int(pred[5])
                    label = model.names[label_idx]
                    confidence = float(pred[4])
                    
                    # Only consider high-confidence detections
                    if confidence < 0.4:
                        continue
                        
                    if any(weapon in label.lower() for weapon in ["gun", "knife", "pistol", "rifle", "sword"]):
                        weapon_detected = True
                        break
            else:
                # Simple color/shape based detection (less accurate)
                # Convert to HSV for better color detection
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                
                # Detect dark objects (could be guns)
                lower_black = np.array([0, 0, 0])
                upper_black = np.array([180, 255, 30])
                mask = cv2.inRange(hsv, lower_black, upper_black)
                
                # Find contours in the mask
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Check if any contour looks like a weapon (simple approximation)
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area < 500:  # Ignore small contours
                        continue
                        
                    # Get bounding rectangle
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w) / h
                    
                    # A gun typically has aspect ratio > 1.5 and < 4
                    if 1.5 < aspect_ratio < 4:
                        weapon_detected = True
                        break

            if weapon_detected:
                break

        cap.release()
        return weapon_detected
    except Exception as e:
        print(f"❌ Error in weapon detection: {e}")
        traceback.print_exc()
        return False

# Function to diagnose camera access
def diagnose_camera_access():
    """Comprehensive camera access diagnosis"""
    print("🔍 Camera Access Diagnostic Report")
    print("-" * 40)
    
    # System Information
    print(f"Operating System: {platform.system()}")
    print(f"Python Version: {platform.python_version()}")
    print(f"OpenCV Version: {cv2.__version__}")
    
    # Camera Detection
    working_cameras = []
    for index in range(5):  # Try more camera indices
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)  # Use DirectShow on Windows
        if cap.isOpened():
            # Verify camera is actually capturing frames
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                working_cameras.append(index)
                print(f"✅ Working Camera Found at Index {index}")
                print(f"  Frame Size: {frame.shape}")
            cap.release()
    
    if not working_cameras:
        print("❌ No working cameras detected")
        
        # Platform-specific camera troubleshooting
        if platform.system() == "Windows":
            print("\n🔧 Windows Troubleshooting Suggestions:")
            print("1. Check Camera Permissions in Windows Settings")
            print("2. Update Camera Drivers")
            print("3. Verify Camera Works in Windows Camera App")
        elif platform.system() == "Darwin":  # macOS
            print("\n🔧 macOS Troubleshooting Suggestions:")
            print("1. Check Privacy & Security Camera Permissions")
            print("2. Verify Camera in Photo Booth")
        elif platform.system() == "Linux":
            print("\n🔧 Linux Troubleshooting Suggestions:")
            print("1. Check V4L2 Kernel Modules")
            print("2. Verify Camera with 'v4l2-ctl --list-devices'")
    
    return working_cameras