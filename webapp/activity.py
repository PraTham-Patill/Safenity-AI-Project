import os
import json
import logging
import uuid
from datetime import datetime
from config import HISTORY_FILE
from history import load_detection_history, get_detection_stats

# Set up logging
logger = logging.getLogger(__name__)

# Path for activity log file
ACTIVITY_LOG_FILE = os.path.join(os.path.dirname(HISTORY_FILE), 'activity_log.json')

def load_activity_log():
    """Load activity log from file"""
    try:
        if os.path.exists(ACTIVITY_LOG_FILE):
            with open(ACTIVITY_LOG_FILE, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"Activity log file not found: {ACTIVITY_LOG_FILE}")
            return []
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error loading activity log file: {e}")
        return []

def save_activity_log(activities):
    """Save activity log to file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(ACTIVITY_LOG_FILE), exist_ok=True)
        
        with open(ACTIVITY_LOG_FILE, 'w') as f:
            json.dump(activities, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving activity log: {e}")
        return False

def log_activity(activity_type, title, description, user_id=None):
    """Log a new activity"""
    try:
        activities = load_activity_log()
        
        # Create new activity entry
        now = datetime.now()
        
        activity = {
            "id": str(uuid.uuid4()),
            "type": activity_type,
            "title": title,
            "description": description,
            "user_id": user_id,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "timestamp": now.timestamp()
        }
        
        # Add to activities and save
        activities.append(activity)
        
        # Keep only the most recent 100 activities
        if len(activities) > 100:
            activities = sorted(activities, key=lambda x: x.get('timestamp', 0), reverse=True)[:100]
        
        save_activity_log(activities)
        logger.info(f"Logged activity: {title}")
        return activity
    except Exception as e:
        logger.error(f"Error logging activity: {e}")
        return None

def get_recent_activities(limit=5):
    """Get recent activities"""
    try:
        # Get activities from activity log
        activities = load_activity_log()
        
        # If no activities in log, generate from detection history
        if not activities:
            activities = generate_activities_from_history()
        
        # Sort by timestamp (newest first) and limit
        activities = sorted(activities, key=lambda x: x.get('timestamp', 0), reverse=True)[:limit]
        
        return activities
    except Exception as e:
        logger.error(f"Error getting recent activities: {e}")
        return []

def generate_activities_from_history():
    """Generate activities from detection history"""
    try:
        # Get detection history
        detection_history = load_detection_history()
        activities = []
        
        # Convert detections to activities
        for detection in detection_history:
            activity_type = "detection"
            crime_detected = detection.get('crime_detected', False)
            crime_label = detection.get('crime_label', 'Unknown')
            
            if crime_detected:
                title = f"{crime_label} Detected"
                description = f"Criminal activity detected in {detection.get('file_name', 'video')}"
                activity_type = "alert"
            else:
                title = "Normal Activity Analyzed"
                description = f"No criminal activity detected in {detection.get('file_name', 'video')}"
            
            # Create activity entry
            activity = {
                "id": detection.get('id', str(uuid.uuid4())),
                "type": activity_type,
                "title": title,
                "description": description,
                "crime_detected": crime_detected,
                "date": detection.get('date'),
                "time": detection.get('time'),
                "timestamp": detection.get('timestamp')
            }
            
            activities.append(activity)
        
        # Add some system activities if needed
        if len(activities) < 5:
            # Add login activity
            now = datetime.now()
            login_time = now.timestamp() - 3600  # 1 hour ago
            
            activities.append({
                "id": str(uuid.uuid4()),
                "type": "login",
                "title": "System Login",
                "description": "You logged into CrimeVision AI",
                "date": now.strftime("%Y-%m-%d"),
                "time": datetime.fromtimestamp(login_time).strftime("%H:%M:%S"),
                "timestamp": login_time
            })
            
            # Add location update activity
            location_time = now.timestamp() - 86400  # 1 day ago
            
            activities.append({
                "id": str(uuid.uuid4()),
                "type": "location",
                "title": "Location Updated",
                "description": "Your default location was updated",
                "date": now.strftime("%Y-%m-%d"),
                "time": datetime.fromtimestamp(location_time).strftime("%H:%M:%S"),
                "timestamp": location_time
            })
        
        # Save these generated activities
        save_activity_log(activities)
        
        return activities
    except Exception as e:
        logger.error(f"Error generating activities from history: {e}")
        return []

def clear_activity_log():
    """Clear all activities"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(ACTIVITY_LOG_FILE), exist_ok=True)
        
        # Write empty array to file
        with open(ACTIVITY_LOG_FILE, 'w') as f:
            json.dump([], f)
        logger.info("Activity log cleared")
        return True
    except Exception as e:
        logger.error(f"Error clearing activity log: {e}")
        return False