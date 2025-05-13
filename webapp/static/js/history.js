document.addEventListener('DOMContentLoaded', function() {
    console.log("History page loaded");
    
    // Debug thumbnails
    const thumbnailImages = document.querySelectorAll('.history-thumbnail img');
    console.log(`Found ${thumbnailImages.length} thumbnail images`);
    
    thumbnailImages.forEach((img, index) => {
        console.log(`Thumbnail ${index} source: ${img.src.substring(0, 50)}...`);
        
        img.addEventListener('error', function() {
            console.error(`Thumbnail ${index} failed to load:`, this.src.substring(0, 100) + '...');
            // Replace with no-thumbnail div
            const noThumbnail = document.createElement('div');
            noThumbnail.className = 'no-thumbnail';
            noThumbnail.innerHTML = '<i class="fas fa-file-video"></i>';
            this.parentNode.replaceChild(noThumbnail, this);
        });
        
        img.addEventListener('load', function() {
            console.log(`Thumbnail ${index} loaded successfully`);
        });
    });
    
    // History filtering functionality
    const historyFilter = document.getElementById('history-filter');
    if (historyFilter) {
        historyFilter.addEventListener('change', function() {
            const filterValue = this.value;
            const historyItems = document.querySelectorAll('.history-item');
            
            historyItems.forEach(item => {
                const detectionType = item.querySelector('.detection-type');
                if (filterValue === 'all') {
                    item.style.display = 'flex';
                } else if (filterValue === 'crime' && detectionType.classList.contains('alert')) {
                    item.style.display = 'flex';
                } else if (filterValue === 'normal' && detectionType.classList.contains('normal')) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
});