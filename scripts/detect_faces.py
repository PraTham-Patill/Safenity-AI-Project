import os
import sys
import cv2
import argparse
import logging
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from webapp.detection import FaceExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'face_detection.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Extract faces from videos or images')
    parser.add_argument('input', help='Path to input video or image file')
    parser.add_argument('--output', help='Path to output directory', default='suspects')
    parser.add_argument('--min-size', help='Minimum face size (width, height)', type=int, default=30)
    parser.add_argument('--confidence', help='Detection confidence threshold', type=float, default=0.5)
    return parser.parse_args()

def extract_faces(file_path, output_dir='suspects', min_size=30, confidence=0.5):
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize face extractor
    face_extractor = FaceExtractor()
    face_extractor.save_path = output_dir
    
    # Extract faces
    logger.info(f"Extracting faces from: {file_path}")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_base = f"suspect_{timestamp}"
    
    face_files = face_extractor.extract(file_path, filename_base)
    
    logger.info(f"Extracted {len(face_files)} faces to {output_dir}")
    return face_files

def main():
    args = parse_arguments()
    
    # Extract faces
    face_files = extract_faces(
        args.input,
        output_dir=args.output,
        min_size=args.min_size,
        confidence=args.confidence
    )
    
    if face_files:
        logger.info("Face extraction completed successfully")
        for face_file in face_files:
            logger.info(f"Saved face: {face_file}")
    else:
        logger.warning("No faces detected or extraction failed")

if __name__ == "__main__":
    main()