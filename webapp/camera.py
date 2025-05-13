import cv2
import time
import platform
import subprocess
import os
from datetime import datetime, timedelta
from config import logger

def diagnose_camera_access():
    """Comprehensive camera access diagnosis"""
    print("🔍 Camera Access Diagnostic Report")
    print("-" * 40)
    
    # System Information
    print(f"Operating System: {platform.system()}")
    print(f"Python Version: {platform.python_version()}")
    print(f"OpenCV Version: {cv2.__version__}")
    
    # Camera Detection
    working_cameras = []
    for index in range(5):  # Try more camera indices
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)  # Use DirectShow on Windows
        if cap.isOpened():
            # Verify camera is actually capturing frames
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                working_cameras.append(index)
                print(f"✅ Working Camera Found at Index {index}")
                print(f"  Frame Size: {frame.shape}")
            cap.release()
    
    if not working_cameras:
        print("❌ No working cameras detected")
        
        # Platform-specific camera troubleshooting
        if platform.system() == "Windows":
            print("\n🔧 Windows Troubleshooting Suggestions:")
            print("1. Check Camera Permissions in Windows Settings")
            print("2. Update Camera Drivers")
            print("3. Verify Camera Works in Windows Camera App")
        elif platform.system() == "Darwin":  # macOS
            print("\n🔧 macOS Troubleshooting Suggestions:")
            print("1. Check Privacy & Security Camera Permissions")
            print("2. Verify Camera in Photo Booth")
        elif platform.system() == "Linux":
            print("\n🔧 Linux Troubleshooting Suggestions:")
            print("1. Check V4L2 Kernel Modules")
            print("2. Verify Camera with 'v4l2-ctl --all'")
    
    return working_cameras

def alternative_camera_capture(camera_index=0, duration=10, output_path=None):
    """Improved camera capture with backend prioritization"""
    try:
        # Prioritize backends based on OS
        backends = []
        if platform.system() == "Windows":
            backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
        elif platform.system() == "Linux":
            backends = [cv2.CAP_V4L2, cv2.CAP_GSTREAMER, cv2.CAP_ANY]
        else:
            backends = [cv2.CAP_ANY]

        for backend in backends:
            cap = cv2.VideoCapture(camera_index, backend)
            if not cap.isOpened():
                continue

            # Set video properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)

            # Verify property settings
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            fps = cap.get(cv2.CAP_PROP_FPS)
            print(f"Using backend: {backend} with {width}x{height} @ {fps} FPS")

            # Prepare video writer
            if not output_path:
                output_path = os.path.join(
                    os.path.expanduser("~"),
                    f"live_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                )
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (int(width), int(height)))
            if not out.isOpened():
                cap.release()
                continue

            start_time = datetime.now()
            frame_count = 0

            while (datetime.now() - start_time).total_seconds() < duration:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame.size == 0:
                    continue
                out.write(frame)
                frame_count += 1

            cap.release()
            out.release()
            print(f"Captured {frame_count} frames")
            return output_path, frame_count

        return None, 0
    except Exception as e:
        print(f"⚠️ Camera capture error: {e}")
        return None, 0