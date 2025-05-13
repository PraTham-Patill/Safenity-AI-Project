// Add this to your existing JavaScript file or create a new one
document.addEventListener('DOMContentLoaded', function() {
    // Get the upload form
    const uploadForm = document.querySelector('form');
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            // Get the send_alert checkbox
            const sendAlertCheckbox = document.getElementById('send_alert');
            
            if (sendAlertCheckbox) {
                // Log the current state for debugging
                console.log('Send Alert checkbox checked:', sendAlertCheckbox.checked);
                
                // Ensure the value is set correctly based on checked state
                if (sendAlertCheckbox.checked) {
                    // Create a hidden input to ensure the value is sent correctly
                    const hiddenInput = document.createElement('input');
                    hiddenInput.type = 'hidden';
                    hiddenInput.name = 'send_alert';
                    hiddenInput.value = 'on';
                    uploadForm.appendChild(hiddenInput);
                    
                    // For debugging
                    console.log('Added hidden input with value "on"');
                }
            }
        });
    }
});