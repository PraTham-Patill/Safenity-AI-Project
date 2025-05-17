# CrimeVision-AI: Crime Detection and Alert System

## Overview
CrimeVision-AI is an advanced crime detection system that uses artificial intelligence to identify criminal activities in videos and images. The system can detect various types of crimes, extract faces of potential suspects, detect weapons, and send SMS alerts to authorities or designated contacts.

## Features

- **Crime Detection**: Uses a ResNet-based deep learning model to classify videos/images into different crime categories
- **Suspect Identification**: Extracts and saves faces of potential suspects from crime footage
- **Weapon Detection**: Identifies potential weapons in crime scenes
- **SMS Alerts**: Sends immediate notifications when crimes are detected
- **History Tracking**: Maintains a comprehensive history of all detections
- **Live Camera Integration**: Supports real-time crime detection through webcam
- **User-friendly Interface**: Modern web interface for easy interaction

## Project Structure

```
CrimeVision-AI/
├── logs/                  # Log files and detection history
├── models/                # Trained AI models
├── scripts/               # Python scripts for detection and training
├── suspects/              # Extracted suspect face images
├── uploads/               # Uploaded videos and images
├── webapp/                # Flask web application
│   ├── static/            # CSS, JavaScript, and images
│   ├── templates/         # HTML templates
│   ├── app.py             # Main Flask application
│   ├── config.py          # Configuration settings
│   ├── detection.py       # Crime detection logic
│   └── ...                # Other utility modules
└── README.md              # Project documentation
```

## Technologies Used

- **Backend**: Python, Flask
- **AI/ML**: TensorFlow, OpenCV, ResNet
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Notifications**: Twilio SMS API

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Webcam (for live detection)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/PraTham-Patill/CrimeVision-AI-Project.git
   cd CrimeVision-AI-Project
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure SMS alerts (optional):
   - Create a `.env` file in the project root
   - Add your Twilio credentials and phone numbers

5. Run the application:
   ```
   python webapp/app.py
   ```

6. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

### Upload Mode
1. From the home page, select "Upload Video/Image"
2. Choose a file from your computer
3. Enable face detection and SMS alerts if needed
4. Click "Upload and Detect"
5. View the detection results

### Live Detection
1. From the home page, select "Live Detection"
2. Grant camera permissions when prompted
3. The system will analyze the video feed in real-time
4. Detection results will be displayed on screen

### History
1. Click on "History" in the navigation menu
2. View all previous detections with thumbnails
3. Click on any entry to see detailed results

## Crime Classes

The system can detect the following types of activities:
- Abuse
- Arrest
- Arson
- Assault
- Burglary
- Explosion
- Fighting
- Normal Activity
- Road Accident
- Robbery
- Shooting
- Shoplifting
- Stealing
- Vandalism

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- ResNet architecture for deep learning
- OpenCV for computer vision tasks
- Flask for web framework
- Twilio for SMS notifications

## Contact

For any inquiries, please contact [patilpratham241@gmail.com](mailto:patilpratham241@gmail.com)
