import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration settings for the Flask application"""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-for-development')
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov'}
    
    # Model paths
    CRIME_MODEL_PATH = os.environ.get('CRIME_MODEL_PATH', os.path.join('models', 'crime_detection_model.h5'))
    WEAPON_MODEL_PATH = os.environ.get('WEAPON_MODEL_PATH', os.path.join('models', 'weapon_detection_model.h5'))
    
    # Detection settings
    CRIME_THRESHOLD = float(os.environ.get('CRIME_THRESHOLD', '0.5'))
    WEAPON_THRESHOLD = float(os.environ.get('WEAPON_THRESHOLD', '0.5'))
    
    # SMS notification settings
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    NOTIFICATION_PHONE_NUMBER = os.environ.get('NOTIFICATION_PHONE_NUMBER')
    
    # Face detection settings
    FACE_MIN_SIZE = int(os.environ.get('FACE_MIN_SIZE', '30'))
    FACE_SAVE_PATH = 'suspects'