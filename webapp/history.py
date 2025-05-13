import os
import json
import logging
import uuid
from datetime import datetime
from config import CLASS_LABELS, HISTORY_FILE

logger = logging.getLogger(__name__)

def load_detection_history():
    """Load detection history from file"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
                if not history:  # If history is empty
                    history = []  # Start with an empty history
                return history
        else:
            logger.warning(f"History file not found: {HISTORY_FILE}")
            return []
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error loading history file: {e}")
        return []

def save_to_history(file_path, crime_class, confidence, detection_id=None, thumbnail=None, source=None, severity_level=None):
    """Save detection to history file"""
    # Ensure directory exists
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    
    history = load_detection_history()
    
    # Create a new entry
    now = datetime.now()
    
    # Determine if this is an uploaded file or recorded video if source not provided
    file_name = os.path.basename(file_path)
    if source is None:
        source = "recorded" if "recorded_" in file_name else "uploaded"
    
    # Generate ID if not provided
    entry_id = detection_id or str(uuid.uuid4())
    
    # Check if this detection already exists in history
    # Look for entries with the same file_path or detection_id
    existing_entry = None
    for entry in history:
        # Check if same detection_id or same file path
        if entry.get('id') == entry_id or entry.get('file_path') == file_path:
            existing_entry = entry
            logger.info(f"Found existing entry for {file_name} with ID: {entry.get('id')}")
            break
    
    # If entry exists, update it instead of creating a new one
    if existing_entry:
        # Update the existing entry with new information
        existing_entry.update({
            "crime_class": int(crime_class),
            "crime_label": CLASS_LABELS.get(int(crime_class), "Unknown"),
            "confidence": round(float(confidence) * 100, 2),
            "crime_detected": int(crime_class) != 7,  # 7 is "Normal Videos"
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "timestamp": now.timestamp()
        })
        
        # Only update thumbnail if provided and not already set
        if thumbnail and not existing_entry.get('thumbnail'):
            existing_entry["thumbnail"] = thumbnail
            
        # Only update source if provided and not already set
        if source and not existing_entry.get('source'):
            existing_entry["source"] = source
            
        logger.info(f"Updated existing detection in history with ID: {existing_entry['id']}")
        entry = existing_entry
    else:
        # Create a new entry
        entry = {
            "id": entry_id,
            "file_path": file_path,
            "file_name": file_name,
            "crime_class": int(crime_class),
            "crime_label": CLASS_LABELS.get(int(crime_class), "Unknown"),
            "confidence": round(float(confidence) * 100, 2),
            "crime_detected": int(crime_class) != 7,  # 7 is "Normal Videos"
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "timestamp": now.timestamp(),
            "thumbnail": thumbnail,
            "source": source
        }
        
        # Add to history
        history.append(entry)
        logger.info(f"Added new detection to history with ID: {entry['id']}")
    
    # Sort all entries by timestamp (newest first)
    history = sorted(history, key=lambda x: x.get('timestamp', 0), reverse=True)
    
    # Keep only the most recent 100 entries
    if len(history) > 100:
        history = history[:100]
    
    # Save the updated history to file
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    
    return entry

def clear_history():
    """Clear all detection history"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        
        # Write empty array to file
        with open(HISTORY_FILE, 'w') as f:
            json.dump([], f)
        logger.info("Detection history cleared")
        return True
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        return False

def delete_detection(detection_id):
    """Delete a detection from history"""
    try:
        detection_history = load_detection_history()
        
        # Filter out the detection to delete
        updated_history = [d for d in detection_history if d.get('id') != detection_id]
        
        # Save the updated history
        with open(HISTORY_FILE, 'w') as f:
            json.dump(updated_history, f, indent=2)
        
        logger.info(f"Deleted detection with ID: {detection_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting detection: {e}")
        return False

def get_detection_stats():
    """Get statistics about crime detections"""
    try:
        detection_history = load_detection_history()
        
        # Initialize stats
        stats = {
            "total_detections": len(detection_history),
            "crime_detected": 0,
            "normal_detected": 0,
            "crime_types": {},
            "recent_detections": []
        }
        
        # Calculate stats
        for detection in detection_history:
            if detection.get('crime_detected'):
                stats["crime_detected"] += 1
            else:
                stats["normal_detected"] += 1
                
            # Count by crime type
            crime_label = detection.get('crime_label')
            if crime_label:
                if crime_label in stats["crime_types"]:
                    stats["crime_types"][crime_label] += 1
                else:
                    stats["crime_types"][crime_label] = 1
        
        # Get 5 most recent detections
        sorted_history = sorted(detection_history, key=lambda x: x.get('timestamp', 0), reverse=True)
        stats["recent_detections"] = sorted_history[:5]
        
        return stats
    except Exception as e:
        logger.error(f"Error getting detection stats: {e}")
        return {
            "total_detections": 0,
            "crime_detected": 0,
            "normal_detected": 0,
            "crime_types": {},
            "recent_detections": []
        }

def search_history(query=None, crime_type=None, date_from=None, date_to=None):
    """Search detection history with filters"""
    try:
        detection_history = load_detection_history()
        
        # Filter results
        results = []
        for detection in detection_history:
            # Text search
            if query and not any(query in str(v).lower() for v in detection.values()):
                continue
                
            # Crime type filter
            if crime_type:
                if crime_type == 'crime' and not detection.get('crime_detected'):
                    continue
                elif crime_type == 'normal' and detection.get('crime_detected'):
                    continue
                elif crime_type not in ['crime', 'normal'] and detection.get('crime_label') != crime_type:
                    continue
            
            # Date range filter
            if date_from or date_to:
                detection_date = detection.get('date')
                if date_from and detection_date < date_from:
                    continue
                if date_to and detection_date > date_to:
                    continue
            
            results.append(detection)
        
        # Sort by timestamp (newest first)
        results = sorted(results, key=lambda x: x.get('timestamp', 0), reverse=True)
        
        return results
    except Exception as e:
        logger.error(f"Error searching history: {e}")
        return []

def get_detection_by_id(detection_id):
    """Get a specific detection by ID"""
    try:
        detection_history = load_detection_history()
        for detection in detection_history:
            if detection.get('id') == detection_id:
                return detection
        return None
    except Exception as e:
        logger.error(f"Error getting detection by ID: {e}")
        return None