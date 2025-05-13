import os
import cv2
import time
import traceback
import base64
import platform
import numpy as np
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from werkzeug.utils import secure_filename

# Import from our modules
from config import (
    UPLOAD_FOLDER, SUSPECTS_FOLDER, CLASS_LABELS, 
    SMS_ENABLED, logger, project_dir
)
from utils import validate_phone_number, get_platform_specific_codec
from history import (
    load_detection_history, save_to_history, get_detection_stats, 
    delete_detection, clear_history
)
from camera import diagnose_camera_access, alternative_camera_capture
from detection import detect_crime, extract_suspect_faces, detect_weapon
from sms import send_sms_alert, send_sms_via_twilio
from activity import get_recent_activities, log_activity, generate_activities_from_history

# Initialize Flask App
app = Flask(__name__, template_folder="../webapp/templates", static_folder="../webapp/static")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config['SUSPECTS_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'suspects')

# Helper function for error pages
def render_error_page(error_message):
    """Render a simple error page when templates fail"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Error</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f8f9fa;
            }}
            .error-container {{
                max-width: 800px;
                margin: 50px auto;
                background-color: white;
                border-radius: 5px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 20px;
            }}
            h1 {{
                color: #dc3545;
            }}
            .error-message {{
                background-color: #f8d7da;
                color: #721c24;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .back-button {{
                display: inline-block;
                background-color: #007bff;
                color: white;
                padding: 10px 15px;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="error-container">
            <h1>Error Occurred</h1>
            <div class="error-message">
                {error_message}
            </div>
            <a href="/" class="back-button">Back to Home</a>
        </div>
    </body>
    </html>
    """
    return html

# Basic Routes
@app.route("/")
def home():
    return render_template("index.html")  

@app.route("/settings")
def settings():
    """Display settings page"""
    return render_template("settings.html")

@app.route("/history")
def history():
    """Display detection history page"""
    try:
        detection_history = load_detection_history()
        # Sort by timestamp (newest first)
        detection_history = sorted(detection_history, key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # Debug history entries
        logger.info(f"Loaded {len(detection_history)} history entries")
        for i, entry in enumerate(detection_history[:5]):  # Log first 5 entries
            source = entry.get('source', 'unknown')
            file_name = entry.get('file_name', 'unknown')
            has_thumbnail = 'thumbnail' in entry and entry['thumbnail'] is not None
            logger.info(f"Entry {i}: source={source}, file={file_name}, has_thumbnail={has_thumbnail}")
            
        return render_template("history.html", detection_history=detection_history)
    except Exception as e:
        logger.error(f"Error loading history: {e}")
        return render_template("history.html", detection_history=[], error=str(e))


@app.route("/view-detection/<detection_id>")
def view_detection(detection_id):
    """View a specific detection from history"""
    try:
        detection_history = load_detection_history()
        detection = next((d for d in detection_history if d.get('id') == detection_id), None)
        
        if not detection:
            return render_template("error.html", error_message="Detection not found"), 404
        
        # Extract data from the detection entry
        crime_class_index = detection.get('crime_class', 7)  # Default to Normal Videos
        crime_class_name = detection.get('crime_label', 'Unknown')
        confidence = detection.get('confidence', 0)
        timestamp_str = f"{detection.get('date', '')} {detection.get('time', '')}"
        file_path = detection.get('file_name', '')
        
        # Check if there are any suspect faces for this detection
        suspect_faces = []
        if 'suspect_faces' in detection:
            suspect_faces = detection['suspect_faces']
        
        # Check if weapon was detected
        weapon_detected = detection.get('weapon_detected', False)
        
        # Check if SMS was sent
        sms_sent = detection.get('sms_sent', False)
        
        # Render the result template with the detection data
        return render_template(
            "result.html",
            crime_label=crime_class_name,
            confidence=f"{confidence}",
            timestamp=timestamp_str,
            file_path=file_path,
            suspect_faces=suspect_faces,
            weapon_detected=weapon_detected,
            sms_sent=sms_sent,
            detection_id=detection_id,
            crime_class=crime_class_index,
            file_type=detection.get('file_type', 'video'),
            suspect_count=len(suspect_faces) if suspect_faces else 0,
            from_history=True  # Flag to indicate this is being viewed from history
        )
    except Exception as e:
        logger.error(f"Error viewing detection: {e}")
        return render_template("error.html", error_message=str(e)), 500

# File Upload and Processing Routes
@app.route("/detect", methods=["POST"])
def upload():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        file_ext = os.path.splitext(file.filename)[1].lower()
        valid_extensions = ['.jpg', '.jpeg', '.png', '.mp4', '.avi', '.mov', '.mkv']
        if file_ext not in valid_extensions:
            return jsonify({"error": f"Invalid file type. Allowed types: {', '.join(valid_extensions)}"}), 400

        # Get processing options with better form value handling
        enable_face_detection = request.form.get("face-detection", "off") == "on"
        
        # Improved handling of send_alert value from form
        send_alert_value = request.form.get("send-alert", "off")
        logger.info(f"Received send_alert value: '{send_alert_value}'")
        
        # Check for multiple possible "true" values from different form types
        send_alert = send_alert_value in ["on", "true", "1", "yes", True]
        logger.info(f"SMS alerts enabled by user: {send_alert}")
        
        # Create timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        secure_filename = f"{timestamp}_{os.path.basename(file.filename)}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
        print(f"File saved: {file_path}")

        # Detect crime (without severity level)
        crime_class_index, prediction_score = detect_crime(file_path)
        crime_class_index = int(crime_class_index)
        prediction_score = float(prediction_score) * 100
        crime_class_name = CLASS_LABELS.get(crime_class_index, "Unknown Crime")
        is_crime = crime_class_index != 7  # Not "Normal Videos"
        
        # Set default severity level based on crime class
        severity_level = 2 if is_crime else 0
        severity_text = {
            0: "None",
            1: "Low",
            2: "Medium",
            3: "High"
        }.get(severity_level, "Unknown")
        print(f"Detected: {crime_class_name} ({prediction_score:.2f}%), is crime: {is_crime}")

        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        is_video = file_ext in ['.mp4', '.avi', '.mov', '.mkv']
        
        # Only extract faces and detect weapons if it's a crime and a video
        suspect_faces = []
        weapon_detected = False
        
        if is_crime and is_video:  # Not "Normal Videos" and is a video
            suspect_faces = extract_suspect_faces(file_path)
            print(f"Found {len(suspect_faces)} suspect faces")
            
            weapon_detected = detect_weapon(file_path)
            print(f"Weapon detected: {weapon_detected}")

        # Improved SMS sending logic with comprehensive logging
        sms_sent = False
        
        # Log all conditions for sending SMS
        logger.info(f"SMS sending conditions: user_enabled={send_alert}, is_crime={is_crime}, system_enabled={SMS_ENABLED}")
        
        # Only send if all three conditions are met
        if send_alert and is_crime and SMS_ENABLED:
            logger.info("All conditions met for sending SMS alert - attempting to send now")
            try:
                # Prepare alert message
                alert_message = f"⚠️ CRIME ALERT: {crime_class_name} detected with {prediction_score:.2f}% confidence at {timestamp_str}."
                if weapon_detected:
                    alert_message += " WARNING: Potential weapon detected!"
                if len(suspect_faces) > 0:
                    alert_message += f" {len(suspect_faces)} suspect(s) identified."
                
                # Send the alert
                sms_sent = send_sms_alert(
                    crime_class_name, 
                    prediction_score, 
                    timestamp_str, 
                    len(suspect_faces), 
                    weapon_detected
                )
                logger.info(f"SMS alert sent successfully: {sms_sent}")
            except Exception as e:
                logger.error(f"Error sending SMS alert: {e}")
                sms_sent = False
        else:
            # Detailed logging of why SMS was not sent
            reasons = []
            if not send_alert:
                reasons.append("alerts disabled by user")
            if not is_crime:
                reasons.append("normal activity detected (not a crime)")
            if not SMS_ENABLED:
                reasons.append("SMS system disabled in configuration")
            
            reason_str = " and ".join(reasons)
            logger.info(f"SMS alert not sent because: {reason_str}")
                
        # Create a thumbnail for history
        try:
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                # Resize the frame to a smaller thumbnail size
                thumbnail_size = (320, 180)  # 16:9 aspect ratio
                thumbnail_frame = cv2.resize(frame, thumbnail_size)
                
                # Convert to base64 for storage
                _, buffer = cv2.imencode('.jpg', thumbnail_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                thumbnail_data = base64.b64encode(buffer).decode('utf-8')
                
                # Store as data URL format
                thumbnail = f"data:image/jpeg;base64,{thumbnail_data}"
                logger.info("Successfully created thumbnail for uploaded file")
            else:
                logger.warning("Could not read frame from video for thumbnail")
                thumbnail = None
            cap.release()
        except Exception as e:
            logger.error(f"Error creating video thumbnail: {e}")
            thumbnail = None

        # Save to history with thumbnail
        detection_id = timestamp.replace(":", "").replace("-", "").replace(" ", "")
        
        try:
            # Import here to avoid circular imports
            from history import save_to_history
            # Include thumbnail in the save_to_history call and explicitly mark as uploaded
            save_to_history(file_path, crime_class_index, prediction_score/100, detection_id, thumbnail, source="uploaded")
            logger.info(f"Saved uploaded file to history with ID: {detection_id} and thumbnail")
        except Exception as e:
            logger.error(f"Error saving to history: {e}")
            # Try without thumbnail as fallback
            try:
                from history import save_to_history
                save_to_history(file_path, crime_class_index, prediction_score/100, detection_id, source="uploaded")
                logger.info(f"Saved to history with ID: {detection_id} (without thumbnail)")
            except Exception as e2:
                logger.error(f"Error saving to history without thumbnail: {e2}")

        return render_template(
            "result.html",
            crime_label=crime_class_name,
            confidence=f"{prediction_score:.2f}",
            timestamp=timestamp_str,
            file_path=secure_filename,
            suspect_faces=[os.path.basename(face) for face in suspect_faces],
            weapon_detected=weapon_detected,
            sms_sent=sms_sent
        )
    except Exception as e:
        print(f"Error in upload route: {e}")
        return render_template("error.html", error_message=str(e)), 500

# Camera and Live Detection Routes
@app.route('/capture_live_video', methods=['POST'])
def capture_live_video():
    """Robust live video recording with frame verification"""
    try:
        # Create a unique output path
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(app.config["UPLOAD_FOLDER"], f"live_{timestamp}.mp4")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        logger.info(f"Starting video capture process to {output_path}")
        
        # Force release any existing camera instances
        cv2.destroyAllWindows()
        time.sleep(1)
        
        # Try multiple potential backends
        working_camera = None
        for backend in [cv2.CAP_ANY, cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_V4L2]:
            try:
                logger.info(f"Trying camera with backend {backend}")
                camera = cv2.VideoCapture(0, backend)
                
                if camera.isOpened():
                    # Verify we get real frames with content
                    for _ in range(10):  # Try multiple times for warmup
                        ret, frame = camera.read()
                        if ret and frame is not None and frame.size > 0:
                            # Check if frame has actual content (not just black)
                            if frame.mean() > 1.0:  # Non-black frames have higher mean values
                                logger.info(f"Camera providing valid frames with backend {backend}")
                                working_camera = camera
                                break
                        time.sleep(0.1)
                    
                    if working_camera:
                        break
                    else:
                        logger.warning(f"Camera opened but frames are empty or black with backend {backend}")
                        camera.release()
                else:
                    logger.warning(f"Failed to open camera with backend {backend}")
            except Exception as e:
                logger.error(f"Error with backend {backend}: {e}")
                if 'camera' in locals() and camera:
                    camera.release()
        
        if not working_camera:
            logger.error("Failed to get valid frames from any camera backend")
            return jsonify({
                "success": False,
                "error": "Could not get valid video frames from camera. Please check camera permissions."
            }), 500
        
        # Set camera properties
        working_camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        working_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        working_camera.set(cv2.CAP_PROP_FPS, 30)
        
        # Get actual properties
        width = int(working_camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(working_camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = working_camera.get(cv2.CAP_PROP_FPS)
        
        logger.info(f"Camera properties: {width}x{height} @ {fps} FPS")
        
        # Get platform-specific codec
        fourcc = cv2.VideoWriter_fourcc(*get_platform_specific_codec())
        
        # Initialize video writer
        out = cv2.VideoWriter(
            output_path, 
            fourcc, 
            fps if fps > 0 else 30, 
            (width, height)
        )
        
        if not out.isOpened():
            working_camera.release()
            logger.error("Failed to initialize video writer")
            
            # Try an alternative codec as fallback
            alternative_fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(
                output_path, 
                alternative_fourcc, 
                fps if fps > 0 else 30, 
                (width, height)
            )
            
            if not out.isOpened():
                logger.error("Failed to initialize video writer with fallback codec")
                return jsonify({
                    "success": False,
                    "error": "Failed to initialize video recording. Try a different format."
                }), 500
        
        # Record for 10 seconds
        duration = 10  # seconds
        start_time = time.time()
        frame_count = 0
        
        logger.info(f"Recording for {duration} seconds...")
        
        while time.time() - start_time < duration:
            ret, frame = working_camera.read()
            if not ret or frame is None or frame.size == 0:
                continue
                
            out.write(frame)
            frame_count += 1
            
            # Provide progress feedback every second
            elapsed = time.time() - start_time
            if int(elapsed) > int(elapsed - 0.1):
                logger.info(f"Recording: {int(elapsed)}/{duration} seconds, {frame_count} frames captured")
        
        # Release resources
        working_camera.release()
        out.release()
        cv2.destroyAllWindows()
        
        logger.info(f"Recording complete: {frame_count} frames captured to {output_path}")
        
        if frame_count < 10:
            logger.warning("Very few frames captured, video may be invalid")
            return jsonify({
                "success": False,
                "error": "Very few frames captured. Please check your camera."
            }), 500
        
        # Process the recorded video
        return jsonify({
            "success": True,
            "file_path": os.path.basename(output_path),
            "message": f"Video recorded successfully with {frame_count} frames."
        })
        
    except Exception as e:
        logger.error(f"Error in video capture: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/video_feed')
def video_feed():
    """Real-time video streaming with crime detection"""
    def generate_frames():
        camera = None
        for backend in [cv2.CAP_DSHOW, cv2.CAP_ANY]:
            camera = cv2.VideoCapture(0, backend)
            if camera.isOpened():
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                break
        if not camera or not camera.isOpened():
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n')
            return

        # For performance, only run detection every N frames
        frame_count = 0
        detection_interval = 30  # Adjust based on performance
        current_crime_class = 7  # Start with "Normal Videos"
        current_confidence = 0.0
        
        try:
            while True:
                success, frame = camera.read()
                if not success:
                    break
                    
                # Increment frame counter
                frame_count += 1
                
                # Run detection periodically
                if frame_count % detection_interval == 0:
                    try:
                        # Save frame temporarily
                        temp_path = os.path.join(app.config["UPLOAD_FOLDER"], "temp_frame.jpg")
                        cv2.imwrite(temp_path, frame)
                        
                        # Run detection
                        crime_class_index, prediction_score = detect_crime(temp_path)
                        current_crime_class = int(crime_class_index)
                        current_confidence = float(prediction_score) * 100
                        
                        # Clean up
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                    except Exception as e:
                        logger.error(f"Error in detection: {e}")
                
                # Add detection info to frame
                crime_class_name = CLASS_LABELS.get(current_crime_class, "Unknown")
                is_crime = current_crime_class != 7  # Not "Normal Videos"
                
                # Add text overlay
                status_color = (0, 0, 255) if is_crime else (0, 255, 0)  # Red for crime, green for normal
                cv2.putText(frame, f"Status: {'CRIME DETECTED' if is_crime else 'Normal'}", 
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
                cv2.putText(frame, f"Class: {crime_class_name}", 
                            (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, f"Confidence: {current_confidence:.2f}%", 
                            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Convert to JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    continue
                    
                # Yield the frame in the response
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                
        finally:
            if camera:
                camera.release()

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/record_video', methods=['GET'])
def record_video():
    """Page for recording video directly from the camera"""
    return render_template('record_video.html')

@app.route('/save_recorded_video', methods=['POST'])
def save_recorded_video():
    """Save a video recorded in the browser"""
    try:
        # Check if the post has the file part
        if 'video_blob' not in request.files:
            return jsonify({"error": "No video data received"}), 400
            
        video_file = request.files['video_blob']
        
        # Create a unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Try to save as mp4 if possible, otherwise use webm
        try:
            # First save the original webm
            webm_filename = f"recorded_{timestamp}.webm"
            webm_path = os.path.join(app.config["UPLOAD_FOLDER"], webm_filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(webm_path), exist_ok=True)
            
            # Save the file
            video_file.save(webm_path)
            
            # For analysis, extract a frame
            jpg_filename = f"recorded_{timestamp}.jpg"
            jpg_path = os.path.join(app.config["UPLOAD_FOLDER"], jpg_filename)
            
            # Create a thumbnail for history - FIX: Use webm_path instead of undefined file_path
            try:
                cap = cv2.VideoCapture(webm_path)  # Changed from file_path to webm_path
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    # Resize the frame to a smaller thumbnail size
                    thumbnail_size = (320, 180)  # 16:9 aspect ratio
                    thumbnail_frame = cv2.resize(frame, thumbnail_size)
                    
                    # Convert to base64 for storage
                    _, buffer = cv2.imencode('.jpg', thumbnail_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    thumbnail_data = base64.b64encode(buffer).decode('utf-8')
                    
                    # Store as data URL format
                    thumbnail = f"data:image/jpeg;base64,{thumbnail_data}"
                    logger.info("Successfully created thumbnail for recorded video")
                else:
                    logger.warning("Could not read frame from video for thumbnail")
                    thumbnail = None
                cap.release()
            except Exception as e:
                logger.error(f"Error creating video thumbnail: {e}")
                thumbnail = None
                
            # Detect crime on the saved frame
            crime_class_index, prediction_score = detect_crime(jpg_path)
            crime_class_index = int(crime_class_index)
            prediction_score = float(prediction_score)
            
            # Save to history with thumbnail
            detection_id = timestamp.replace(":", "").replace("-", "").replace(" ", "")
            
            try:
                # Include thumbnail in the save_to_history call
                from history import save_to_history
                save_to_history(webm_path, crime_class_index, prediction_score, detection_id, thumbnail)
                logger.info(f"Saved recorded video to history with ID: {detection_id} and thumbnail")
            except Exception as e:
                logger.error(f"Error saving recorded video to history: {e}")
                
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    cv2.imwrite(jpg_path, frame)
                    logger.info(f"Saved frame from video to {jpg_filename}")
                    # Use the jpg for analysis
                    return jsonify({
                        "success": True,
                        "message": "Video saved successfully",
                        "filename": jpg_filename,
                        "redirect": f"/process_recorded_video?filename={jpg_filename}"
                    })
                cap.release()
            
            # If we couldn't extract a frame, use the original webm
            return jsonify({
                "success": True,
                "message": "Video saved successfully",
                "filename": webm_filename,
                "redirect": f"/process_recorded_video?filename={webm_filename}"
            })
            
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            return jsonify({"error": str(e)}), 500
            
    except Exception as e:
        logger.error(f"Error saving recorded video: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/process_recorded_video', methods=['GET'])
def process_recorded_video():
    """Process a recorded video file"""
    try:
        filename = request.args.get('filename')
        if not filename:
            return render_template("error.html", error_message="No filename provided"), 400
            
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        logger.info(f"Processing recorded video: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return render_template("error.html", error_message=f"File {filename} not found"), 404
        
        # Get default values for processing options
        enable_face_detection = True
        send_alert = False
        
        # Create timestamp for tracking
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if it's a video file
        file_ext = os.path.splitext(filename)[1].lower()
        is_video = file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        
        # Log file details
        logger.info(f"File exists: {os.path.exists(file_path)}")
        logger.info(f"File size: {os.path.getsize(file_path)} bytes")
        logger.info(f"Is video: {is_video}")
        
        # For webm files, convert to mp4 first
        if file_ext == '.webm':
            try:
                logger.info("Converting webm to mp4 for better compatibility")
                mp4_filename = os.path.splitext(filename)[0] + '.mp4'
                mp4_path = os.path.join(app.config["UPLOAD_FOLDER"], mp4_filename)
                
                # Try to use a frame from the webm file for analysis instead of conversion
                logger.info("Attempting to extract a frame from webm for analysis")
                cap = cv2.VideoCapture(file_path)
                success = False
                
                if cap.isOpened():
                    # Try to read a few frames to find a good one
                    for _ in range(10):
                        ret, frame = cap.read()
                        if ret and frame is not None and frame.size > 0:
                            # Save this frame as a jpg for analysis
                            jpg_filename = os.path.splitext(filename)[0] + '.jpg'
                            jpg_path = os.path.join(app.config["UPLOAD_FOLDER"], jpg_filename)
                            cv2.imwrite(jpg_path, frame)
                            logger.info(f"Successfully extracted frame to {jpg_path}")
                            file_path = jpg_path
                            filename = jpg_filename
                            success = True
                            break
                    cap.release()
                
                if not success:
                    logger.warning("Could not extract frame from webm, using original file")
                    # Continue with original file
            except Exception as e:
                logger.error(f"Error handling webm file: {e}")
                # Continue with original file
        
        # Only try to convert video files, not images
        if is_video and file_ext != '.jpg' and file_ext != '.jpeg' and file_ext != '.png':
            try:
                # Use OpenCV to convert the file
                mp4_filename = os.path.splitext(filename)[0] + '.mp4'
                mp4_path = os.path.join(app.config["UPLOAD_FOLDER"], mp4_filename)
                
                cap = cv2.VideoCapture(file_path)
                if not cap.isOpened():
                    logger.error("Could not open video file with OpenCV")
                    return render_template("error.html", error_message="Could not process video file"), 500
                
                # Get video properties
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                if fps <= 0:
                    fps = 30  # Default to 30fps if not detected
                
                # Create video writer
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(mp4_path, fourcc, fps, (width, height))
                
                # Process frames
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    out.write(frame)
                
                # Release resources
                cap.release()
                out.release()
                
                # Use the mp4 file for further processing
                file_path = mp4_path
                filename = mp4_filename
                logger.info(f"Converted to mp4: {file_path}")
            except Exception as e:
                logger.error(f"Error converting video: {e}")
                # Continue with original file if conversion fails
        
        # Detect crime with improved error handling
        try:
            logger.info("Running crime detection on recorded video...")
            crime_class_index, prediction_score = detect_crime(file_path)
            crime_class_index = int(crime_class_index)
            prediction_score = float(prediction_score) * 100
            crime_class_name = CLASS_LABELS.get(crime_class_index, "Unknown Crime")
            logger.info(f"Detected: {crime_class_name} ({prediction_score:.2f}%)")
        except Exception as detect_error:
            logger.error(f"Error during crime detection of recorded video: {detect_error}")
            traceback.print_exc()
            return render_template("error.html", 
                                  error_message=f"Error analyzing the recorded video: {str(detect_error)}"), 500
        
        # Only extract faces and detect weapons if it's a crime and a video
        suspect_faces = []
        weapon_detected = False
        
        if crime_class_index != 7 and is_video and enable_face_detection:  # Not "Normal Videos" and is a video
            try:
                suspect_faces = extract_suspect_faces(file_path)
                logger.info(f"Found {len(suspect_faces)} suspect faces")
                
                weapon_detected = detect_weapon(file_path)
                logger.info(f"Weapon detected: {weapon_detected}")
            except Exception as e:
                logger.error(f"Error in face/weapon detection: {e}")
                traceback.print_exc()
        
        # In the thumbnail creation section, update the code to ensure proper thumbnail creation:
        
        # Create a thumbnail for history
        try:
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                # Resize the frame to a smaller thumbnail size
                thumbnail_size = (320, 180)  # 16:9 aspect ratio
                thumbnail_frame = cv2.resize(frame, thumbnail_size)
                
                # Convert to base64 for storage
                _, buffer = cv2.imencode('.jpg', thumbnail_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                thumbnail_data = base64.b64encode(buffer).decode('utf-8')
                
                # Store as data URL format
                thumbnail = f"data:image/jpeg;base64,{thumbnail_data}"
                logger.info("Successfully created thumbnail")
            else:
                logger.warning("Could not read frame from video for thumbnail")
                thumbnail = None
            cap.release()
        except Exception as e:
            logger.error(f"Error creating video thumbnail: {e}")
            thumbnail = None
        
        # Save to history with thumbnail
        detection_id = timestamp.replace(":", "").replace("-", "").replace(" ", "")
        
        try:
            # Include thumbnail in the save_to_history call
            save_to_history(file_path, crime_class_index, prediction_score/100, detection_id, thumbnail)
            logger.info(f"Saved to history with ID: {detection_id} and thumbnail")
        except Exception as e:
            logger.error(f"Error saving to history: {e}")
            # Try without thumbnail as fallback
            try:
                save_to_history(file_path, crime_class_index, prediction_score/100, detection_id)
                logger.info(f"Saved to history with ID: {detection_id} (without thumbnail)")
            except Exception as e2:
                logger.error(f"Error saving to history without thumbnail: {e2}")
        
        # Return the result page
        return render_template(
            "result.html",
            crime_label=crime_class_name,
            confidence=f"{prediction_score:.2f}",
            timestamp=timestamp_str,
            file_path=filename,
            suspect_faces=[os.path.basename(face) for face in suspect_faces],
            weapon_detected=weapon_detected,
            sms_sent=False,
            detection_id=detection_id,
            crime_class=crime_class_index,
            file_type="video",
            suspect_count=len(suspect_faces),
            face_detection_enabled=enable_face_detection,
            alert_enabled=send_alert
        )
    except Exception as e:
        logger.error(f"Error processing recorded video: {e}")
        traceback.print_exc()
        return render_template("error.html", error_message=f"Error processing video: {str(e)}"), 500

@app.route('/live_detection')
def live_detection():
    """Page for live crime detection from camera"""
    return render_template('live_detection.html')

@app.route('/report-incident', methods=['POST'])
def report_incident():
    """Handle incident reports from both live detection and result pages"""
    try:
        # Get form data
        phone_number = request.form.get('phone_number')
        incident_message = request.form.get('incident_message')
        is_emergency = request.form.get('emergency_alert') == 'on'
        
        # Get optional crime details if available
        crime_label = request.form.get('crime_label', 'Unknown')
        confidence = request.form.get('confidence', 'N/A')
        weapon_detected = request.form.get('weapon_detected', 'No')
        suspect_count = request.form.get('suspect_count', '0')
        
        # Validate inputs
        if not phone_number or not incident_message:
            return jsonify({
                "success": False,
                "error": "Phone number and incident message are required"
            }), 400
            
        # Validate phone number format
        if not validate_phone_number(phone_number):
            return jsonify({
                "success": False,
                "error": "Invalid phone number format. Please include country code (e.g., +1)"
            }), 400
        
        # Prepare message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = "🚨 EMERGENCY ALERT: " if is_emergency else "⚠️ INCIDENT REPORT: "
        
        # Create a more detailed message with crime information if available
        message = f"{prefix}{incident_message}\n\n"
        
        # Add crime details if available
        if crime_label != 'Unknown' and crime_label != 'Normal Videos':
            message += f"Crime Type: {crime_label}\n"
            message += f"Confidence: {confidence}%\n"
            message += f"Weapon Detected: {weapon_detected}\n"
            message += f"Suspects Identified: {suspect_count}\n\n"
            
        message += f"Reported at: {timestamp}"
        
        # Send SMS via Twilio
        success, result = send_sms_via_twilio(phone_number, message)
        
        if success:
            logger.info(f"Incident report sent successfully to {phone_number}")
            return jsonify({
                "success": True,
                "message": "Incident report sent successfully"
            })
        else:
            logger.error(f"Failed to send incident report: {result}")
            return jsonify({
                "success": False,
                "error": f"Failed to send SMS: {result}"
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing incident report: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# History Management Routes
@app.route('/delete-detection/<detection_id>', methods=['POST'])
def delete_detection_route(detection_id):
    """Delete a detection from history"""
    try:
        success = delete_detection(detection_id)
        return jsonify({"success": success})
    except Exception as e:
        logger.error(f"Error deleting detection: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/clear-history', methods=['POST'])
def clear_history_route():
    """Clear all detection history"""
    try:
        success = clear_history()
        return jsonify({"success": success})
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# SMS and Reporting Routes
@app.route("/send_report", methods=["POST"])
def send_report():
    try:
        # Get data from request
        data = request.json
        recipient = data.get("recipient")
        message = data.get("message")
        
        if not recipient or not message:
            return jsonify({"success": False, "error": "Missing recipient or message"}), 400
            
        # Validate phone number
        if not validate_phone_number(recipient):
            return jsonify({"success": False, "error": "Invalid phone number format"}), 400
            
        # Send SMS
        success, result = send_sms_via_twilio(recipient, message)
        
        if success:
            return jsonify({"success": True, "message": "Report sent successfully", "sid": result})
        else:
            return jsonify({"success": False, "error": result}), 400
            
    except Exception as e:
        logger.error(f"Error sending report: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# API Endpoints
@app.route('/api/history')
def api_history():
    """API endpoint to get detection history as JSON"""
    try:
        detection_history = load_detection_history()
        # Sort by timestamp (newest first)
        detection_history = sorted(detection_history, key=lambda x: x.get('timestamp', 0), reverse=True)
        return jsonify(detection_history)
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def api_stats():
    """API endpoint to get crime detection statistics"""
    try:
        stats = get_detection_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error retrieving stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/clear-history', methods=['POST'])
def api_clear_history():
    """Clear all detection history"""
    try:
        success = clear_history()
        return jsonify({"success": success})
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/delete-detection/<detection_id>', methods=['DELETE'])
def api_delete_detection(detection_id):
    """Delete a specific detection from history"""
    try:
        success = delete_detection(detection_id)
        return jsonify({"success": success})
    except Exception as e:
        logger.error(f"Error deleting detection: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/export-history')
def export_history():
    """Export detection history as downloadable JSON file"""
    try:
        detection_history = load_detection_history()
        
        # Create a response with the JSON data
        response = app.response_class(
            response=json.dumps(detection_history, indent=2),
            status=200,
            mimetype='application/json'
        )
        
        # Set headers for file download
        response.headers["Content-Disposition"] = f"attachment; filename=crime_detection_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        return response
    except Exception as e:
        logger.error(f"Error exporting history: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/search-history')
def search_history():
    """Search detection history"""
    try:
        query = request.args.get('q', '').lower()
        
        if not query:
            return jsonify({"error": "No search query provided"}), 400
            
        crime_type = request.args.get('type')
        date_from = request.args.get('from')
        date_to = request.args.get('to')
        
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
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error searching history: {e}")
        return jsonify({"error": str(e)}), 500

# Route for Crime News
@app.route('/crime-news')
def crime_news():
    """Page for crime news and alerts"""
    return render_template('crime-news.html')

# Route for Emergency Contacts
@app.route('/emergency-contacts')
def emergency_contacts():
    """Page for emergency contacts"""
    return render_template('emergency-contacts.html')

# Route for Police Stations
@app.route('/police-stations')
def police_stations():
    """Page for nearby police stations"""
    return render_template('police-stations.html')

# Route for Cybersecurity
@app.route('/cybersecurity')
def cybersecurity():
    """Page for cybersecurity information"""
    return render_template('cybersecurity.html')

# Route for Legal Resources
@app.route('/legal-resources')
def legal_resources():
    """Page for legal resources and information"""
    return render_template('legal-resources.html')

# Route for Safety Tools
@app.route('/safety-tools')
def safety_tools():
    """Page for personal safety tools and tips"""
    return render_template('safety-tools.html')

# Serve Uploaded Files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Serve Suspect Faces
@app.route('/suspects/<filename>')
def suspect_face(filename):
    """Serve suspect face images"""
    return send_from_directory(app.config['SUSPECTS_FOLDER'], filename)

# Add this route as an alias to the existing suspect_face route
@app.route('/suspect_files/<filename>')
def suspect_file(filename):
    """Alias for suspect_face route"""
    return suspect_face(filename)

# Add a route for the dashboard

@app.route("/dashboard")
def dashboard():
    """Display dashboard with crime detection statistics"""
    try:
        stats = get_detection_stats()
        return render_template("dashboard.html", stats=stats)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template("dashboard.html", stats={
            "total_detections": 0,
            "crime_detected": 0,
            "normal_detected": 0,
            "crime_types": {},
            "recent_detections": []
        }, error=str(e))

# Add a route for the SOS emergency feature
@app.route('/sos', methods=['POST'])
def sos_emergency():
    """Handle SOS emergency alerts"""
    try:
        data = request.json
        location = data.get('location', {})
        user_info = data.get('userInfo', {})
        
        # Log the emergency
        logger.info(f"SOS Emergency triggered by {user_info.get('name', 'Unknown User')}")
        logger.info(f"Location: Lat {location.get('latitude')}, Long {location.get('longitude')}")
        
        # Here you would typically:
        # 1. Send SMS to emergency contacts
        # 2. Notify nearest police station
        # 3. Store the emergency in database
        
        # For now, we'll just return success
        return jsonify({
            "success": True,
            "message": "Emergency alert sent successfully",
            "emergencyId": datetime.now().strftime("%Y%m%d%H%M%S")
        })
    except Exception as e:
        logger.error(f"Error processing SOS emergency: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# Add a health check endpoint
@app.route('/health')
def health_check():
    """API health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

# Add a route for the about page
@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

# Add a route for the contact page
@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

# Add a route for the privacy policy
@app.route('/privacy-policy')
def privacy_policy():
    """Privacy policy page"""
    return render_template('privacy-policy.html')

# Add a route for the terms of service
@app.route('/terms-of-service')
def terms_of_service():
    """Terms of service page"""
    return render_template('terms-of-service.html')

# Route for sending emergency messages
@app.route('/send-emergency-message', methods=['POST'])
def send_emergency_message():
    """Send emergency message to all contacts"""
    try:
        data = request.json
        message = data.get('message')
        
        if not message:
            return jsonify({"success": False, "error": "No message provided"}), 400
            
        # Get contacts from localStorage (this would be handled client-side)
        # Here we're just handling the SMS sending part
        
        # Log the emergency message
        logger.info(f"Emergency message triggered: {message[:50]}...")
        
        # In a real implementation, you would retrieve contacts from a database
        # For now, we'll use the SMS function to send to the configured recipient
        if SMS_ENABLED:
            try:
                # Get recipient from config
                recipient = RECIPIENT_PHONE_NUMBER
                
                # Send the message
                success, result = send_sms_via_twilio(recipient, message)
                
                if success:
                    logger.info(f"Emergency message sent successfully")
                    return jsonify({"success": True, "message": "Emergency message sent successfully"})
                else:
                    logger.error(f"Failed to send emergency message: {result}")
                    return jsonify({"success": False, "error": f"Failed to send message: {result}"}), 500
            except Exception as e:
                logger.error(f"Error sending emergency message: {e}")
                return jsonify({"success": False, "error": str(e)}), 500
        else:
            logger.warning("SMS is disabled in configuration, cannot send emergency message")
            return jsonify({"success": False, "error": "SMS functionality is disabled"}), 400
            
    except Exception as e:
        logger.error(f"Error processing emergency message: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# 📌 **Run Flask App**
if __name__ == "__main__":
    print("🚀 Starting Crime Detection Web App...")
    


    print(f"✅ SMS alerts enabled: {'Yes' if SMS_ENABLED else 'No'}")
    
    # Check if templates folder exists
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    if not os.path.exists(templates_dir):
        print(f"⚠️ Warning: Templates directory not found at {templates_dir}")
    else:
        print(f"✅ Templates directory found with {len(os.listdir(templates_dir))} files")
    
    # Check if static folder exists
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if not os.path.exists(static_dir):
        print(f"⚠️ Warning: Static directory not found at {static_dir}")
    else:
        print(f"✅ Static directory found with {len(os.listdir(static_dir))} files")
    
    # Create necessary folders if they don't exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["SUSPECTS_FOLDER"], exist_ok=True)
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)