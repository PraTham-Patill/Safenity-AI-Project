// CrimeVision-AI Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // File upload preview
    const fileInput = document.getElementById('file-input');
    const filePreview = document.getElementById('file-preview');
    const fileDropArea = document.querySelector('.file-drop-area');
    
    if (fileInput && filePreview) {
        fileInput.addEventListener('change', function() {
            previewFile(this.files[0]);
        });
        
        // Drag and drop functionality
        if (fileDropArea) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                fileDropArea.addEventListener(eventName, preventDefaults, false);
            });
            
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            ['dragenter', 'dragover'].forEach(eventName => {
                fileDropArea.addEventListener(eventName, highlight, false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                fileDropArea.addEventListener(eventName, unhighlight, false);
            });
            
            function highlight() {
                fileDropArea.classList.add('highlight');
            }
            
            function unhighlight() {
                fileDropArea.classList.remove('highlight');
            }
            
            fileDropArea.addEventListener('drop', handleDrop, false);
            
            function handleDrop(e) {
                const dt = e.dataTransfer;
                const files = dt.files;
                
                if (files.length) {
                    fileInput.files = files;
                    previewFile(files[0]);
                }
            }
        }
    }
    
    function previewFile(file) {
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = function(e) {
            let preview;
            
            if (file.type.startsWith('image/')) {
                preview = document.createElement('img');
                preview.src = e.target.result;
                preview.classList.add('img-fluid', 'rounded');
            } else if (file.type.startsWith('video/')) {
                preview = document.createElement('video');
                preview.src = e.target.result;
                preview.classList.add('img-fluid', 'rounded');
                preview.controls = true;
            } else {
                preview = document.createElement('div');
                preview.textContent = 'File type not supported for preview';
                preview.classList.add('alert', 'alert-warning');
            }
            
            filePreview.innerHTML = '';
            filePreview.appendChild(preview);
        };
        
        reader.readAsDataURL(file);
    }
    
    // Live detection functionality
    const videoElement = document.getElementById('webcam');
    const startButton = document.getElementById('start-detection');
    const stopButton = document.getElementById('stop-detection');
    const detectionResult = document.getElementById('detection-result');
    
    if (videoElement && startButton && stopButton) {
        let stream = null;
        let detectionInterval = null;
        
        startButton.addEventListener('click', async function() {
            try {
                stream = await navigator.mediaDevices.getUserMedia({ video: true });
                videoElement.srcObject = stream;
                
                startButton.disabled = true;
                stopButton.disabled = false;
                
                // Start detection at intervals
                detectionInterval = setInterval(detectCrime, 3000); // Every 3 seconds
            } catch (err) {
                console.error('Error accessing webcam:', err);
                alert('Could not access webcam. Please make sure you have a webcam connected and have granted permission.');
            }
        });
        
        stopButton.addEventListener('click', function() {
            if (stream) {
                const tracks = stream.getTracks();
                tracks.forEach(track => track.stop());
                videoElement.srcObject = null;
                
                startButton.disabled = false;
                stopButton.disabled = true;
                
                // Stop detection interval
                if (detectionInterval) {
                    clearInterval(detectionInterval);
                    detectionInterval = null;
                }
                
                // Clear detection result
                if (detectionResult) {
                    detectionResult.textContent = '';
                    detectionResult.className = 'detection-overlay';
                }
            }
        });
        
        async function detectCrime() {
            if (!stream || !videoElement.srcObject) return;
            
            // Create a canvas to capture the current video frame
            const canvas = document.createElement('canvas');
            canvas.width = videoElement.videoWidth;
            canvas.height = videoElement.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
            
            // Convert canvas to blob
            canvas.toBlob(async function(blob) {
                // Create a file from the blob
                const file = new File([blob], 'live-detection.jpg', { type: 'image/jpeg' });
                
                // Create form data
                const formData = new FormData();
                formData.append('image', file);
                
                try {
                    // Send to backend API
                    const response = await fetch('/api/detect', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    // Update UI with detection result
                    if (detectionResult) {
                        if (result.crime_detected && result.crime_type !== 'Normal Activity') {
                            detectionResult.textContent = `${result.crime_type} Detected (${Math.round(result.confidence * 100)}%)`;
                            detectionResult.className = 'detection-overlay bg-danger';
                            
                            // If weapon is also detected
                            if (result.weapon_detected) {
                                detectionResult.textContent += ` - ${result.weapon_type} Detected`;
                            }
                        } else {
                            detectionResult.textContent = 'No Crime Detected';
                            detectionResult.className = 'detection-overlay bg-success';
                        }
                    }
                } catch (err) {
                    console.error('Error during detection:', err);
                }
            }, 'image/jpeg');
        }
    }
});
