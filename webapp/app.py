import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import logging
from datetime import datetime
from dotenv import load_dotenv

# Import local modules
from config import Config
from detection import CrimeDetector, WeaponDetector, FaceExtractor
from notifications import SMSNotifier

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'app.log')),
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
crime_detector = CrimeDetector(model_path=os.path.join('models', 'crime_detection_model.h5'))
weapon_detector = WeaponDetector(model_path=os.path.join('models', 'weapon_detection_model.h5'))
face_extractor = FaceExtractor()

# Initialize SMS notifier if credentials are available
sms_notifier = None
if os.getenv('TWILIO_ACCOUNT_SID') and os.getenv('TWILIO_AUTH_TOKEN'):
    from notifications import SMSNotifier
    sms_notifier = SMSNotifier(
        account_sid=os.getenv('TWILIO_ACCOUNT_SID'),
        auth_token=os.getenv('TWILIO_AUTH_TOKEN'),
        from_number=os.getenv('TWILIO_PHONE_NUMBER'),
        to_number=os.getenv('NOTIFICATION_PHONE_NUMBER')
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
            
        file = request.files['file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
            
        if file:
            # Save the uploaded file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            saved_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
            file.save(file_path)
            
            # Process the file for crime detection
            detect_faces = 'detect_faces' in request.form
            send_sms = 'send_sms' in request.form
            
            # Perform crime detection
            crime_result = crime_detector.detect(file_path)
            
            # Perform weapon detection if crime detected
            weapon_result = None
            if crime_result['crime_detected'] and crime_result['crime_type'] != 'Normal Activity':
                weapon_result = weapon_detector.detect(file_path)
            
            # Extract faces if requested and crime detected
            faces = []
            if detect_faces and crime_result['crime_detected'] and crime_result['crime_type'] != 'Normal Activity':
                faces = face_extractor.extract(file_path, saved_filename)
            
            # Send SMS notification if requested and crime detected
            sms_sent = False
            if send_sms and sms_notifier and crime_result['crime_detected'] and crime_result['crime_type'] != 'Normal Activity':
                message = f"ALERT: {crime_result['crime_type']} detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                if weapon_result and weapon_result['weapon_detected']:
                    message += f". Weapon detected: {weapon_result['weapon_type']}"
                sms_sent = sms_notifier.send_alert(message)
            
            # Log the detection
            logger.info(f"Detection: {crime_result['crime_type']} | File: {saved_filename} | Faces: {len(faces)} | SMS: {sms_sent}")
            
            # Save detection to history
            history_entry = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'filename': saved_filename,
                'file_path': file_path,
                'crime_detected': crime_result['crime_detected'],
                'crime_type': crime_result['crime_type'],
                'confidence': crime_result['confidence'],
                'weapon_detected': weapon_result['weapon_detected'] if weapon_result else False,
                'weapon_type': weapon_result['weapon_type'] if weapon_result and weapon_result['weapon_detected'] else None,
                'faces_extracted': len(faces),
                'sms_sent': sms_sent
            }
            
            # Save history to file
            with open(os.path.join('logs', 'detection_history.json'), 'a') as f:
                import json
                f.write(json.dumps(history_entry) + '\n')
            
            return render_template('result.html', 
                                  result=crime_result, 
                                  weapon_result=weapon_result,
                                  faces=faces,
                                  filename=saved_filename,
                                  sms_sent=sms_sent)
    
    return render_template('upload.html')

@app.route('/live')
def live():
    return render_template('live.html')

@app.route('/api/detect', methods=['POST'])
def api_detect():
    # This endpoint is used by the live detection feature
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400
        
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    # Save the uploaded file temporarily
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_filename = f"{timestamp}_{filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
    file.save(file_path)
    
    # Perform crime detection
    crime_result = crime_detector.detect(file_path)
    
    # Perform weapon detection if crime detected
    weapon_result = None
    if crime_result['crime_detected'] and crime_result['crime_type'] != 'Normal Activity':
        weapon_result = weapon_detector.detect(file_path)
    
    # Clean up temporary file
    os.remove(file_path)
    
    return jsonify({
        'crime_detected': crime_result['crime_detected'],
        'crime_type': crime_result['crime_type'],
        'confidence': crime_result['confidence'],
        'weapon_detected': weapon_result['weapon_detected'] if weapon_result else False,
        'weapon_type': weapon_result['weapon_type'] if weapon_result and weapon_result['weapon_detected'] else None
    })

@app.route('/history')
def history():
    # Read detection history from file
    history_entries = []
    history_file = os.path.join('logs', 'detection_history.json')
    
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            import json
            for line in f:
                if line.strip():
                    history_entries.append(json.loads(line))
    
    # Sort by timestamp (newest first)
    history_entries.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('history.html', history=history_entries)

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
