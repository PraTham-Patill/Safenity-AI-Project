import os
import sys
import cv2
import numpy as np
import argparse
import logging
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from webapp.detection import CrimeDetector, WeaponDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'detection.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Detect crimes in videos or images')
    parser.add_argument('input', help='Path to input video or image file')
    parser.add_argument('--output', help='Path to output directory', default='outputs')
    parser.add_argument('--crime-model', help='Path to crime detection model', 
                        default=os.path.join('models', 'crime_detection_model.h5'))
    parser.add_argument('--weapon-model', help='Path to weapon detection model', 
                        default=os.path.join('models', 'weapon_detection_model.h5'))
    parser.add_argument('--threshold', help='Detection confidence threshold', type=float, default=0.5)
    parser.add_argument('--save-frames', help='Save frames with detections', action='store_true')
    return parser.parse_args()

def process_file(file_path, crime_detector, weapon_detector, threshold=0.5, save_frames=False, output_dir='outputs'):
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Process based on file type
    if file_path.lower().endswith(('.mp4', '.avi', '.mov')):
        return process_video(file_path, crime_detector, weapon_detector, threshold, save_frames, output_dir)
    else:
        return process_image(file_path, crime_detector, weapon_detector, threshold, save_frames, output_dir)

def process_image(image_path, crime_detector, weapon_detector, threshold, save_frames, output_dir):
    logger.info(f"Processing image: {image_path}")
    
    # Detect crime
    crime_result = crime_detector.detect(image_path)
    logger.info(f"Crime detection result: {crime_result}")
    
    # Detect weapon if crime detected
    weapon_result = None
    if crime_result['crime_detected'] and crime_result['confidence'] > threshold:
        weapon_result = weapon_detector.detect(image_path)
        logger.info(f"Weapon detection result: {weapon_result}")
    
    # Save annotated image if requested
    if save_frames and crime_result['crime_detected'] and crime_result['confidence'] > threshold:
        img = cv2.imread(image_path)
        # Add detection info to image
        text = f"{crime_result['crime_type']} ({crime_result['confidence']:.2f})"
        if weapon_result and weapon_result['weapon_detected']:
            text += f" - {weapon_result['weapon_type']} ({weapon_result['confidence']:.2f})"
        
        cv2.putText(img, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Save the annotated image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"{timestamp}_detection.jpg")
        cv2.imwrite(output_path, img)
        logger.info(f"Saved annotated image to {output_path}")
    
    return {
        'crime_result': crime_result,
        'weapon_result': weapon_result
    }

def process_video(video_path, crime_detector, weapon_detector, threshold, save_frames, output_dir):
    logger.info(f"Processing video: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Could not open video file: {video_path}")
        return None
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    
    logger.info(f"Video properties: {fps} fps, {frame_count} frames, {duration:.2f} seconds")
    
    # Initialize results
    results = {
        'crime_detections': [],
        'weapon_detections': [],
        'frames_processed': 0
    }
    
    # Process video frames
    frame_interval = max(1, int(fps))  # Process one frame per second
    frame_number = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Process every nth frame
        if frame_number % frame_interval == 0:
            # Save frame temporarily
            temp_frame_path = os.path.join(output_dir, 'temp_frame.jpg')
            cv2.imwrite(temp_frame_path, frame)
            
            # Detect crime
            crime_result = crime_detector.detect(temp_frame_path)
            
            # Detect weapon if crime detected
            weapon_result = None
            if crime_result['crime_detected'] and crime_result['confidence'] > threshold:
                weapon_result = weapon_detector.detect(temp_frame_path)
            
            # Save results
            if crime_result['crime_detected'] and crime_result['confidence'] > threshold:
                timestamp = frame_number / fps if fps > 0 else 0
                detection = {
                    'frame': frame_number,
                    'timestamp': timestamp,
                    'crime_type': crime_result['crime_type'],
                    'confidence': crime_result['confidence']
                }
                results['crime_detections'].append(detection)
                
                # Save weapon detection if applicable
                if weapon_result and weapon_result['weapon_detected']:
                    weapon_detection = {
                        'frame': frame_number,
                        'timestamp': timestamp,
                        'weapon_type': weapon_result['weapon_type'],
                        'confidence': weapon_result['confidence']
                    }
                    results['weapon_detections'].append(weapon_detection)
                
                # Save frame if requested
                if save_frames:
                    # Add detection info to frame
                    text = f"{crime_result['crime_type']} ({crime_result['confidence']:.2f})"
                    if weapon_result and weapon_result['weapon_detected']:
                        text += f" - {weapon_result['weapon_type']} ({weapon_result['confidence']:.2f})"
                    
                    cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    
                    # Save the annotated frame
                    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_path = os.path.join(output_dir, f"{timestamp_str}_frame_{frame_number}.jpg")
                    cv2.imwrite(output_path, frame)
            
            # Remove temporary frame
            if os.path.exists(temp_frame_path):
                os.remove(temp_frame_path)
            
            results['frames_processed'] += 1
        
        frame_number += 1
    
    cap.release()
    
    # Log summary
    logger.info(f"Processed {results['frames_processed']} frames")
    logger.info(f"Detected {len(results['crime_detections'])} crime instances")
    logger.info(f"Detected {len(results['weapon_detections'])} weapon instances")
    
    return results

def main():
    args = parse_arguments()
    
    # Initialize detectors
    crime_detector = CrimeDetector(model_path=args.crime_model)
    weapon_detector = WeaponDetector(model_path=args.weapon_model)
    
    # Process the input file
    results = process_file(
        args.input, 
        crime_detector, 
        weapon_detector, 
        threshold=args.threshold, 
        save_frames=args.save_frames, 
        output_dir=args.output
    )
    
    if results:
        logger.info("Processing completed successfully")
    else:
        logger.error("Processing failed")

if __name__ == "__main__":
    main()