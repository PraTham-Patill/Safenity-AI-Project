import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from config import Config
from detection import CrimeDetector, WeaponDetector, FaceExtractor
from sms import send_alert

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'webapp.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Ensure required directories exist
for directory in ['uploads', 'suspects', 'logs']:
    os.makedirs(directory, exist_ok=True)

# Initialize detectors
crime_detector = CrimeDetector()
weapon_detector = WeaponDetector()
face_extractor = FaceExtractor()

@app.route('/')
def index():
    """Render the home page"""
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Handle file uploads and detection"""
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        # Get form options
        detect_faces = 'detect_faces' in request.form
        send_sms = 'send_sms' in request.form
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join('uploads', filename)
        file.save(file_path)
        
        logger.info(f"File uploaded: {file_path}")
        
        # Detect crime
        crime_result = crime_detector.detect(file_path)
        logger.info(f"Crime detection result: {crime_result}")
        
        # Detect weapon if crime detected
        weapon_result = None
        if crime_result['crime_detected']:
            weapon_result = weapon_detector.detect(file_path)
            logger.info(f"Weapon detection result: {weapon_result}")
        
        # Extract faces if requested and crime detected
        face_paths = []
        if detect_faces and crime_result['crime_detected']:
            face_paths = face_extractor.extract(file_path)
            logger.info(f"Extracted {len(face_paths)} faces")
        
        # Send SMS alert if requested and crime detected
        sms_sent = False
        if send_sms and crime_result['crime_detected']:
            message = f"ALERT: {crime_result['crime_type']} detected"
            if weapon_result and weapon_result['weapon_detected']:
                message += f" with {weapon_result['weapon_type']}"
            
            sms_sent = send_alert(message)
            logger.info(f"SMS alert sent: {sms_sent}")
        
        # Save detection to history
        history_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'file_path': file_path,
            'crime_result': crime_result,
            'weapon_result': weapon_result,
            'faces_detected': len(face_paths) if face_paths else 0,
            'sms_sent': sms_sent
        }
        
        # Save history entry to log file
        with open(os.path.join('logs', 'detection_history.log'), 'a') as f:
            f.write(f"{history_entry}\n")
        
        return render_template(
            'result.html',
            file_path=file_path,
            crime_result=crime_result,
            weapon_result=weapon_result,
            face_paths=face_paths,
            sms_sent=sms_sent
        )
    
    return render_template('upload.html')

@app.route('/live')
def live():
    """Render the live detection page"""
    return render_template('live_detection.html')

@app.route('/api/detect', methods=['POST'])
def api_detect():
    """API endpoint for live detection"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image provided'}), 400
    
    # Save the uploaded image
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{filename}"
    file_path = os.path.join('uploads', filename)
    file.save(file_path)
    
    # Detect crime
    crime_result = crime_detector.detect(file_path)
    
    # Detect weapon if crime detected
    weapon_result = None
    if crime_result['crime_detected']:
        weapon_result = weapon_detector.detect(file_path)
    
    # Extract faces if crime detected
    face_paths = []
    if crime_result['crime_detected']:
        face_paths = face_extractor.extract(file_path)
    
    # Send SMS alert if crime detected
    sms_sent = False
    if crime_result['crime_detected'] and crime_result['confidence'] > 0.7:  # Higher threshold for alerts
        message = f"ALERT: {crime_result['crime_type']} detected"
        if weapon_result and weapon_result['weapon_detected']:
            message += f" with {weapon_result['weapon_type']}"
        
        sms_sent = send_alert(message)
    
    # Prepare response
    response = {
        'crime_detected': crime_result['crime_detected'],
        'crime_type': crime_result['crime_type'] if crime_result['crime_detected'] else None,
        'crime_confidence': float(crime_result['confidence']) if crime_result['crime_detected'] else 0,
        'weapon_detected': weapon_result['weapon_detected'] if weapon_result else False,
        'weapon_type': weapon_result['weapon_type'] if weapon_result and weapon_result['weapon_detected'] else None,
        'faces_detected': len(face_paths),
        'sms_sent': sms_sent
    }
    
    return jsonify(response)

@app.route('/history')
def history():
    """Display detection history"""
    # Read history from log file
    history_entries = []
    history_file = os.path.join('logs', 'detection_history.log')
    
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            for line in f:
                try:
                    entry = eval(line.strip())  # Convert string representation to dict
                    history_entries.append(entry)
                except Exception as e:
                    logger.error(f"Error parsing history entry: {e}")
    
    # Sort entries by timestamp (newest first)
    history_entries.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('history.html', history=history_entries)

@app.route('/dashboard')
def dashboard():
    """Render the dashboard page"""
    return render_template('dashboard.html')

@app.route('/emergency-contacts')
def emergency_contacts():
    """Render the emergency contacts page"""
    return render_template('emergency-contacts.html')

@app.route('/crime-news')
def crime_news():
    """Render the crime news page"""
    return render_template('crime-news.html')

@app.route('/cybersecurity')
def cybersecurity():
    """Render the cybersecurity page"""
    return render_template('cybersecurity.html')

@app.route('/legal-resources')
def legal_resources():
    """Render the legal resources page"""
    return render_template('legal-resources.html')

@app.route('/safety-tools')
def safety_tools():
    """Render the safety tools page"""
    return render_template('safety-tools.html')

@app.route('/police-stations')
def police_stations():
    """Render the police stations page"""
    return render_template('police-stations.html')

@app.route('/about')
def about():
    """Render the about page"""
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)