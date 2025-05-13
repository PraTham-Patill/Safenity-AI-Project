// Add this to your existing JavaScript file
document.addEventListener('DOMContentLoaded', function() {
    // Get the upload form
    const uploadForm = document.querySelector('form');
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', function() {
            // Get the send_alert checkbox
            const sendAlertCheckbox = document.getElementById('send_alert');
            
            if (sendAlertCheckbox) {
                // Log the current state for debugging
                console.log('Send Alert checkbox checked:', sendAlertCheckbox.checked);
                
                // Ensure the value is set correctly based on checked state
                if (sendAlertCheckbox.checked) {
                    sendAlertCheckbox.value = 'on';
                } else {
                    // Create a hidden input with the same name if unchecked
                    // This ensures the parameter is sent even when unchecked
                    const hiddenInput = document.createElement('input');
                    hiddenInput.type = 'hidden';
                    hiddenInput.name = 'send_alert';
                    hiddenInput.value = 'off';
                    uploadForm.appendChild(hiddenInput);
                }
            }
        });
    }
});