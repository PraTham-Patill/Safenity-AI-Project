import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Path configurations
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.abspath(os.path.join(current_dir, ".."))
scripts_path = os.path.abspath(os.path.join(current_dir, "..", "scripts"))
UPLOAD_FOLDER = os.path.abspath(os.path.join(current_dir, "..", "uploads"))
SUSPECTS_FOLDER = os.path.abspath(os.path.join(current_dir, "..", "suspects"))
LOGS_FOLDER = os.path.abspath(os.path.join(current_dir, "..", "logs"))
HISTORY_FILE = os.path.join(LOGS_FOLDER, "detection_history.json")

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SUSPECTS_FOLDER, exist_ok=True)
os.makedirs(LOGS_FOLDER, exist_ok=True)

# Add paths to sys.path
if scripts_path not in sys.path:
    sys.path.append(scripts_path)
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Twilio SMS Credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
RECIPIENT_PHONE_NUMBER = os.getenv("RECIPIENT_PHONE_NUMBER")
SMS_ENABLED = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER and RECIPIENT_PHONE_NUMBER)

# Crime Labels (UCF Crime Dataset)
CLASS_LABELS = {
    0: "Abuse", 1: "Arrest", 2: "Arson", 3: "Assault", 4: "Burglary",
    5: "Explosion", 6: "Fighting", 7: "Normal Videos", 8: "Road Accidents",
    9: "Robbery", 10: "Shooting", 11: "Shoplifting", 12: "Stealing", 13: "Vandalism"
}

# Initialize history file if it doesn't exist
if not os.path.exists(HISTORY_FILE):
    import json
    with open(HISTORY_FILE, 'w') as f:
        json.dump([], f)