# Safenity AI: Empowering Safety Through Intelligent Surveillance

## Abstract
Safenity AI provides comprehensive crime detection and community safety features through an intuitive web interface. It features an intuitive web dashboard with SOS alerts, emergency contacts, crime updates, cybersecurity tips, legal help, and other safety tools. Detected crime type is shown on the results page for quick assessment and response.

## Objective
Develop a smart surveillance system for real-time crime detection and public safety enhancement.

## System Capabilities
### Crime Classification with ResNet-50
Detects and classifies suspicious activities in surveillance footage using a ResNet-50 model trained on the UCF Crime Dataset.

### Weapon Detection using YOLOv5
Identifies weapons such as knives or guns in video frames using the YOLOv5 object detection algorithm.

### Result Visualization
Displays the detected crime type and suspect visuals clearly on the result page for easy interpretation.

## Key Features
### Live Monitoring Dashboard
Offers real-time crime insights, detection summaries, and visual alerts through a user-friendly web dashboard.

### SOS Emergency Button
Enables users to send quick alerts with live location to emergency contacts in case of danger.

### Quick Emergency Access
Provides direct access to emergency services, personal emergency contacts, and nearby police stations.

### Informative Modules
Includes sections on Cybersecurity Awareness, Legal Rights & Assistance, Crime News & Alerts, and Personal Safety Tools.

## Method/Approach

### Technical Stack
- **Backend**: Python Flask, RESTful APIs
- **Frontend**: HTML5/Bootstrap, JavaScript
- **AI Models**: ResNet-50 (UCF-tuned), YOLOv5, OpenCV

## Results/Findings

| Feature | Description | Impact |
|---------|-------------|--------|
| Incident Classification & Security Alerts | Recognizes and classifies critical threat events | Enables quick and targeted response by authorities |
| Emergency Contacts | Quick access to police, fire, and medical support | Accelerates emergency communication |
| Severity Classification | Labels events as Low / Moderate / High risk | Prioritizes response actions |
| Model | Uses ResNet-50 pretrained on ImageNet and fine-tuned on UCF Crime Dataset | Achieves 89% accuracy in classifying crime types |
| Visual Markers | Highlights suspects and evidence frames (red/blue boxes) | Simplifies analysis and review |

## Project Structure

```
Safenity AI/
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

## Features

- **Crime Detection**: Uses a ResNet-based deep learning model to classify videos/images into different crime categories
- **Suspect Identification**: Extracts and saves faces of potential suspects from crime footage
- **Weapon Detection**: Identifies potential weapons in crime scenes using YOLOv5
- **SMS Alerts**: Sends immediate notifications when crimes are detected
- **History Tracking**: Maintains a comprehensive history of all detections
- **Live Camera Integration**: Supports real-time crime detection through webcam
- **User-friendly Interface**: Modern web interface for easy interaction
- **Emergency Contacts**: Quick access to police, fire, and medical support
- **Cybersecurity Tips**: Information on staying safe online
- **Legal Aid**: Resources for legal assistance
- **Safety Tools**: Additional tools for personal and community safety

## Technologies Used

- **Backend**: Python, Flask, RESTful APIs
- **AI/ML**: TensorFlow, OpenCV, ResNet-50, YOLOv5
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
   git clone https://github.com/PraTham-Patill/Safenity-AI-Project.git
   cd Safenity-AI-Project
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

## Conclusion and Future Work

This project provides real-time crime detection with alerts, report generation, and emergency contact support. Future work includes expanding the dashboard with features like Crime News, Station Locator, Cybersecurity, Legal Aid, and Safety Tools.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- ResNet architecture for deep learning
- OpenCV for computer vision tasks
- Flask for web framework
- Twilio for SMS notifications
- YOLOv5 for object detection
- UCF Crime Dataset for model training

## Contact

For any inquiries, please contact [patilpratham241@gmail.com](mailto:patilpratham241@gmail.com)