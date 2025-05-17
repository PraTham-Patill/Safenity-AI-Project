import os
from datetime import timedelta

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # Crime detection configuration
    CRIME_CLASSES = [
        'Abuse', 'Arrest', 'Arson', 'Assault', 'Burglary', 'Explosion', 
        'Fighting', 'Normal Activity', 'Road Accident', 'Robbery', 'Shooting', 
        'Shoplifting', 'Stealing', 'Vandalism'
    ]
    
    # Weapon detection configuration
    WEAPON_CLASSES = [
        'Knife', 'Gun', 'No Weapon'
    ]
    
    # Face extraction configuration
    FACE_CONFIDENCE_THRESHOLD = 0.5
    FACE_SAVE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'suspects')
    
    # SMS notification configuration
    SMS_ENABLED = bool(os.environ.get('TWILIO_ACCOUNT_SID') and 
                      os.environ.get('TWILIO_AUTH_TOKEN') and 
                      os.environ.get('TWILIO_PHONE_NUMBER') and 
                      os.environ.get('NOTIFICATION_PHONE_NUMBER'))
