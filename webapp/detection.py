import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.preprocessing import image
import logging

logger = logging.getLogger(__name__)

class CrimeDetector:
    """Class for detecting crimes in images and videos"""
    
    def __init__(self, model_path=None):
        """Initialize the crime detector
        
        Args:
            model_path: Path to the trained model file
        """
        if model_path is None:
            model_path = os.path.join('models', 'crime_detection_model.h5')
        
        self.model_path = model_path
        self.model = None
        self.class_names = []
        self.threshold = 0.5
        
        # Load class names
        class_names_path = os.path.join(os.path.dirname(model_path), 'class_names.txt')
        if os.path.exists(class_names_path):
            with open(class_names_path, 'r') as f:
                self.class_names = [line.strip() for line in f.readlines()]
        else:
            # Default class names if file not found
            self.class_names = [
                'Abuse', 'Arrest', 'Arson', 'Assault', 'Burglary', 'Explosion',
                'Fighting', 'Normal', 'RoadAccident', 'Robbery', 'Shooting',
                'Shoplifting', 'Stealing', 'Vandalism'
            ]
        
        # Load model if it exists
        if os.path.exists(model_path):
            try:
                self.model = load_model(model_path)
                logger.info(f"Loaded crime detection model from {model_path}")
            except Exception as e:
                logger.error(f"Error loading model: {e}")
        else:
            logger.warning(f"Model file not found: {model_path}")
    
    def preprocess_image(self, img_path):
        """Preprocess image for model input
        
        Args:
            img_path: Path to the image file
            
        Returns:
            Preprocessed image array
        """
        img = image.load_img(img_path, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        return img_array
    
    def detect(self, file_path):
        """Detect crime in an image or video
        
        Args:
            file_path: Path to the image or video file
            
        Returns:
            Dictionary with detection results
        """
        if self.model is None:
            logger.error("Model not loaded")
            return {
                'crime_detected': False,
                'crime_type': 'Unknown',
                'confidence': 0.0,
                'error': 'Model not loaded'
            }
        
        try:
            # For simplicity, we'll just process the first frame of videos
            if file_path.lower().endswith(('.mp4', '.avi', '.mov')):
                cap = cv2.VideoCapture(file_path)
                ret, frame = cap.read()
                if not ret:
                    logger.error(f"Could not read video file: {file_path}")
                    return {
                        'crime_detected': False,
                        'crime_type': 'Unknown',
                        'confidence': 0.0,
                        'error': 'Could not read video file'
                    }
                
                # Save frame as temporary image
                temp_img_path = os.path.join('uploads', 'temp_frame.jpg')
                cv2.imwrite(temp_img_path, frame)
                img_array = self.preprocess_image(temp_img_path)
                
                # Clean up temporary file
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
            else:
                # Process image directly
                img_array = self.preprocess_image(file_path)
            
            # Make prediction
            predictions = self.model.predict(img_array)
            predicted_class_index = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class_index])
            predicted_class = self.class_names[predicted_class_index]
            
            # Determine if crime is detected (all classes except 'Normal')
            crime_detected = predicted_class != 'Normal' and confidence > self.threshold
            
            return {
                'crime_detected': crime_detected,
                'crime_type': predicted_class,
                'confidence': confidence
            }
            
        except Exception as e:
            logger.error(f"Error during crime detection: {e}")
            return {
                'crime_detected': False,
                'crime_type': 'Unknown',
                'confidence': 0.0,
                'error': str(e)
            }

class WeaponDetector:
    """Class for detecting weapons in images and videos"""
    
    def __init__(self, model_path=None):
        """Initialize the weapon detector
        
        Args:
            model_path: Path to the trained model file
        """
        if model_path is None:
            model_path = os.path.join('models', 'weapon_detection_model.h5')
        
        self.model_path = model_path
        self.model = None
        self.class_names = ['No Weapon', 'Knife', 'Gun', 'Other Weapon']
        self.threshold = 0.5
        
        # Load model if it exists
        if os.path.exists(model_path):
            try:
                self.model = load_model(model_path)
                logger.info(f"Loaded weapon detection model from {model_path}")
            except Exception as e:
                logger.error(f"Error loading model: {e}")
        else:
            logger.warning(f"Model file not found: {model_path}")
    
    def preprocess_image(self, img_path):
        """Preprocess image for model input
        
        Args:
            img_path: Path to the image file
            
        Returns:
            Preprocessed image array
        """
        img = image.load_img(img_path, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        return img_array
    
    def detect(self, file_path):
        """Detect weapons in an image or video
        
        Args:
            file_path: Path to the image or video file
            
        Returns:
            Dictionary with detection results
        """
        if self.model is None:
            logger.error("Model not loaded")
            return {
                'weapon_detected': False,
                'weapon_type': 'Unknown',
                'confidence': 0.0,
                'error': 'Model not loaded'
            }
        
        try:
            # For simplicity, we'll just process the first frame of videos
            if file_path.lower().endswith(('.mp4', '.avi', '.mov')):
                cap = cv2.VideoCapture(file_path)
                ret, frame = cap.read()
                if not ret:
                    logger.error(f"Could not read video file: {file_path}")
                    return {
                        'weapon_detected': False,
                        'weapon_type': 'Unknown',
                        'confidence': 0.0,
                        'error': 'Could not read video file'
                    }
                
                # Save frame as temporary image
                temp_img_path = os.path.join('uploads', 'temp_frame.jpg')
                cv2.imwrite(temp_img_path, frame)
                img_array = self.preprocess_image(temp_img_path)
                
                # Clean up temporary file
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
            else:
                # Process image directly
                img_array = self.preprocess_image(file_path)
            
            # Make prediction
            predictions = self.model.predict(img_array)
            predicted_class_index = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class_index])
            predicted_class = self.class_names[predicted_class_index]
            
            # Determine if weapon is detected (all classes except 'No Weapon')
            weapon_detected = predicted_class != 'No Weapon' and confidence > self.threshold
            
            return {
                'weapon_detected': weapon_detected,
                'weapon_type': predicted_class,
                'confidence': confidence
            }
            
        except Exception as e:
            logger.error(f"Error during weapon detection: {e}")
            return {
                'weapon_detected': False,
                'weapon_type': 'Unknown',
                'confidence': 0.0,
                'error': str(e)
            }

class FaceExtractor:
    """Class for extracting faces from images and videos"""
    
    def __init__(self, save_path=None, min_size=30):
        """Initialize the face extractor
        
        Args:
            save_path: Path to save extracted faces
            min_size: Minimum face size to extract
        """
        self.save_path = save_path if save_path else 'suspects'
        self.min_size = min_size
        
        # Load face detection model (OpenCV's Haar Cascade)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Ensure save directory exists
        os.makedirs(self.save_path, exist_ok=True)
    
    def extract(self, file_path, filename_base=None):
        """Extract faces from an image or video
        
        Args:
            file_path: Path to the image or video file
            filename_base: Base filename for saved faces
            
        Returns:
            List of paths to saved face images
        """
        if filename_base is None:
            # Use original filename as base
            filename_base = os.path.splitext(os.path.basename(file_path))[0]
        
        face_paths = []
        
        try:
            # Process based on file type
            if file_path.lower().endswith(('.mp4', '.avi', '.mov')):
                face_paths = self._extract_from_video(file_path, filename_base)
            else:
                face_paths = self._extract_from_image(file_path, filename_base)
            
            return face_paths
            
        except Exception as e:
            logger.error(f"Error during face extraction: {e}")
            return []
    
    def _extract_from_image(self, image_path, filename_base):
        """Extract faces from an image
        
        Args:
            image_path: Path to the image file
            filename_base: Base filename for saved faces
            
        Returns:
            List of paths to saved face images
        """
        face_paths = []
        
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Could not read image file: {image_path}")
            return face_paths
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(self.min_size, self.min_size)
        )
        
        # Extract and save each face
        for i, (x, y, w, h) in enumerate(faces):
            face_img = img[y:y+h, x:x+w]
            face_filename = f"{filename_base}_face_{i}.jpg"
            face_path = os.path.join(self.save_path, face_filename)
            cv2.imwrite(face_path, face_img)
            face_paths.append(face_path)
        
        return face_paths
    
    def _extract_from_video(self, video_path, filename_base):
        """Extract faces from a video
        
        Args:
            video_path: Path to the video file
            filename_base: Base filename for saved faces
            
        Returns:
            List of paths to saved face images
        """
        face_paths = []
        face_count = 0
        
        # Open video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Could not open video file: {video_path}")
            return face_paths
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Process video frames (sample 1 frame per second)
        frame_interval = max(1, int(fps))
        frame_number = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every nth frame
            if frame_number % frame_interval == 0:
                # Convert to grayscale for face detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Detect faces
                faces = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(self.min_size, self.min_size)
                )
                
                # Extract and save each face
                for (x, y, w, h) in faces:
                    face_img = frame[y:y+h, x:x+w]
                    face_filename = f"{filename_base}_frame_{frame_number}_face_{face_count}.jpg"
                    face_path = os.path.join(self.save_path, face_filename)
                    cv2.imwrite(face_path, face_img)
                    face_paths.append(face_path)
                    face_count += 1
            
            frame_number += 1
        
        cap.release()
        return face_paths