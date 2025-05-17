import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet50 import preprocess_input
import logging

logger = logging.getLogger(__name__)

class CrimeDetector:
    def __init__(self, model_path):
        self.model_path = model_path
        self.model = None
        self.classes = [
            'Abuse', 'Arrest', 'Arson', 'Assault', 'Burglary', 'Explosion', 
            'Fighting', 'Normal Activity', 'Road Accident', 'Robbery', 'Shooting', 
            'Shoplifting', 'Stealing', 'Vandalism'
        ]
        self._load_model()
    
    def _load_model(self):
        try:
            if os.path.exists(self.model_path):
                self.model = load_model(self.model_path)
                logger.info(f"Loaded crime detection model from {self.model_path}")
            else:
                logger.warning(f"Crime detection model not found at {self.model_path}. Using placeholder.")
                # Create a placeholder model for development without the actual model file
                self._create_placeholder_model()
        except Exception as e:
            logger.error(f"Error loading crime detection model: {str(e)}")
            self._create_placeholder_model()
    
    def _create_placeholder_model(self):
        # This is a placeholder model that returns random predictions
        # It's used for development when the actual model file is not available
        logger.info("Using placeholder crime detection model")
        self.model = None
    
    def preprocess_image(self, img_path):
        # Load and preprocess the image for the model
        try:
            if img_path.lower().endswith(('.mp4', '.avi', '.mov')):
                # For videos, extract a frame
                cap = cv2.VideoCapture(img_path)
                ret, frame = cap.read()
                cap.release()
                if not ret:
                    logger.error(f"Could not read video file: {img_path}")
                    return None
                # Convert BGR to RGB
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (224, 224))
            else:
                # For images
                img = image.load_img(img_path, target_size=(224, 224))
                img = image.img_to_array(img)
            
            # Preprocess the image
            img = preprocess_input(img)
            img = np.expand_dims(img, axis=0)
            return img
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            return None
    
    def detect(self, file_path):
        # Detect crime in the given file
        try:
            if self.model is None:
                # Use placeholder predictions if model is not available
                return self._placeholder_prediction()
            
            # Preprocess the image
            preprocessed_img = self.preprocess_image(file_path)
            if preprocessed_img is None:
                return {
                    'crime_detected': False,
                    'crime_type': 'Unknown',
                    'confidence': 0.0
                }
            
            # Make prediction
            predictions = self.model.predict(preprocessed_img)
            predicted_class_index = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class_index])
            predicted_class = self.classes[predicted_class_index]
            
            # Determine if crime is detected (anything other than 'Normal Activity' with confidence > 0.5)
            crime_detected = predicted_class != 'Normal Activity' and confidence > 0.5
            
            return {
                'crime_detected': crime_detected,
                'crime_type': predicted_class,
                'confidence': confidence
            }
        except Exception as e:
            logger.error(f"Error detecting crime: {str(e)}")
            return self._placeholder_prediction()
    
    def _placeholder_prediction(self):
        # Generate a random prediction for development purposes
        import random
        predicted_class = random.choice(self.classes)
        confidence = random.uniform(0.6, 0.95)
        crime_detected = predicted_class != 'Normal Activity'
        
        return {
            'crime_detected': crime_detected,
            'crime_type': predicted_class,
            'confidence': confidence
        }


class WeaponDetector:
    def __init__(self, model_path):
        self.model_path = model_path
        self.model = None
        self.classes = ['Knife', 'Gun', 'No Weapon']
        self._load_model()
    
    def _load_model(self):
        try:
            if os.path.exists(self.model_path):
                self.model = load_model(self.model_path)
                logger.info(f"Loaded weapon detection model from {self.model_path}")
            else:
                logger.warning(f"Weapon detection model not found at {self.model_path}. Using placeholder.")
                self._create_placeholder_model()
        except Exception as e:
            logger.error(f"Error loading weapon detection model: {str(e)}")
            self._create_placeholder_model()
    
    def _create_placeholder_model(self):
        # Placeholder model for development
        logger.info("Using placeholder weapon detection model")
        self.model = None
    
    def preprocess_image(self, img_path):
        # Similar to crime detector preprocessing
        try:
            if img_path.lower().endswith(('.mp4', '.avi', '.mov')):
                cap = cv2.VideoCapture(img_path)
                ret, frame = cap.read()
                cap.release()
                if not ret:
                    logger.error(f"Could not read video file: {img_path}")
                    return None
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (224, 224))
            else:
                img = image.load_img(img_path, target_size=(224, 224))
                img = image.img_to_array(img)
            
            img = preprocess_input(img)
            img = np.expand_dims(img, axis=0)
            return img
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            return None
    
    def detect(self, file_path):
        try:
            if self.model is None:
                return self._placeholder_prediction()
            
            preprocessed_img = self.preprocess_image(file_path)
            if preprocessed_img is None:
                return {
                    'weapon_detected': False,
                    'weapon_type': 'Unknown',
                    'confidence': 0.0
                }
            
            predictions = self.model.predict(preprocessed_img)
            predicted_class_index = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class_index])
            predicted_class = self.classes[predicted_class_index]
            
            weapon_detected = predicted_class != 'No Weapon' and confidence > 0.5
            
            return {
                'weapon_detected': weapon_detected,
                'weapon_type': predicted_class,
                'confidence': confidence
            }
        except Exception as e:
            logger.error(f"Error detecting weapon: {str(e)}")
            return self._placeholder_prediction()
    
    def _placeholder_prediction(self):
        # Random prediction for development
        import random
        predicted_class = random.choice(self.classes)
        confidence = random.uniform(0.6, 0.95)
        weapon_detected = predicted_class != 'No Weapon'
        
        return {
            'weapon_detected': weapon_detected,
            'weapon_type': predicted_class,
            'confidence': confidence
        }


class FaceExtractor:
    def __init__(self):
        # Load OpenCV's pre-trained face detector
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.save_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'suspects')
        os.makedirs(self.save_path, exist_ok=True)
    
    def extract(self, file_path, filename_base):
        try:
            # Load the image or video frame
            if file_path.lower().endswith(('.mp4', '.avi', '.mov')):
                # For videos, extract multiple frames
                return self._extract_from_video(file_path, filename_base)
            else:
                # For images
                img = cv2.imread(file_path)
                if img is None:
                    logger.error(f"Could not read image file: {file_path}")
                    return []
                return self._extract_from_image(img, filename_base)
        except Exception as e:
            logger.error(f"Error extracting faces: {str(e)}")
            return []
    
    def _extract_from_image(self, img, filename_base):
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        face_files = []
        for i, (x, y, w, h) in enumerate(faces):
            # Extract face region with some margin
            face_img = img[max(0, y-20):min(img.shape[0], y+h+20), max(0, x-20):min(img.shape[1], x+w+20)]
            
            # Save the face image
            face_filename = f"{filename_base}_face_{i}.jpg"
            face_path = os.path.join(self.save_path, face_filename)
            cv2.imwrite(face_path, face_img)
            face_files.append(face_path)
        
        return face_files
    
    def _extract_from_video(self, video_path, filename_base):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Could not open video file: {video_path}")
            return []
        
        face_files = []
        frame_count = 0
        max_frames = 10  # Limit the number of frames to process
        
        while cap.isOpened() and frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every 30 frames to avoid duplicates
            if frame_count % 30 == 0:
                faces = self._extract_from_image(frame, f"{filename_base}_frame_{frame_count}")
                face_files.extend(faces)
            
            frame_count += 1
        
        cap.release()
        return face_files
