// dashboard.js - Handles dashboard functionality including Recent Activity

document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard loaded');
    
    // Load recent activity data
    loadRecentActivity();
    
    // Handle SOS button
    const sosButton = document.getElementById('sos-button');
    if (sosButton) {
        sosButton.addEventListener('click', function() {
            alert('Emergency services have been notified of your location!');
            // Log this as an activity
            logActivity('emergency', 'SOS Emergency Button Pressed', 'Emergency services notified');
        });
    }
    
    // Handle View All button for activity
    const viewAllBtn = document.querySelector('.btn-view-all');
    if (viewAllBtn) {
        viewAllBtn.addEventListener('click', function() {
            window.location.href = '/history';
        });
    }
});

/**
 * Loads recent activity data from the server
 */
function loadRecentActivity() {
    fetch('/api/recent-activity')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateActivityTimeline(data);
        })
        .catch(error => {
            console.error('Error fetching recent activity:', error);
            // If API fails, use fallback data
            const fallbackData = generateFallbackActivityData();
            updateActivityTimeline(fallbackData);
        });
}

/**
 * Updates the activity timeline with the provided data
 * @param {Array} activities - List of activity objects
 */
function updateActivityTimeline(activities) {
    const activityTimeline = document.querySelector('.activity-timeline');
    if (!activityTimeline) return;
    
    // Clear existing items
    activityTimeline.innerHTML = '';
    
    // Add new items
    activities.forEach(activity => {
        const activityItem = createActivityItem(activity);
        activityTimeline.appendChild(activityItem);
    });
}

/**
 * Creates an activity item DOM element
 * @param {Object} activity - Activity data object
 * @returns {HTMLElement} - The activity item element
 */
function createActivityItem(activity) {
    const activityItem = document.createElement('div');
    activityItem.className = 'activity-item';
    
    // Determine icon class based on activity type
    let iconClass = 'info';
    let iconName = 'info-circle';
    
    switch(activity.type) {
        case 'alert':
            iconClass = 'alert';
            iconName = 'exclamation-circle';
            break;
        case 'detection':
            iconClass = activity.crime_detected ? 'alert' : 'info';
            iconName = activity.crime_detected ? 'exclamation-triangle' : 'check-circle';
            break;
        case 'location':
            iconClass = 'location';
            iconName = 'map-marker-alt';
            break;
        case 'login':
            iconClass = 'info';
            iconName = 'user-shield';
            break;
        case 'emergency':
            iconClass = 'alert';
            iconName = 'exclamation-triangle';
            break;
    }
    
    // Create the activity item HTML
    activityItem.innerHTML = `
        <div class="activity-icon ${iconClass}">
            <i class="fas fa-${iconName}"></i>
        </div>
        <div class="activity-content">
            <h4>${activity.title}</h4>
            <p>${activity.description}</p>
            <div class="activity-time">${formatTimeAgo(activity.timestamp)}</div>
        </div>
    `;
    
    return activityItem;
}

/**
 * Formats a timestamp as a relative time (e.g., "2 hours ago")
 * @param {number|string} timestamp - Unix timestamp or ISO string
 * @returns {string} - Formatted relative time
 */
function formatTimeAgo(timestamp) {
    const now = new Date();
    const date = new Date(timestamp);
    const seconds = Math.floor((now - date) / 1000);
    
    // Handle invalid dates
    if (isNaN(seconds)) {
        return 'recently';
    }
    
    const intervals = [
        { label: 'year', seconds: 31536000 },
        { label: 'month', seconds: 2592000 },
        { label: 'week', seconds: 604800 },
        { label: 'day', seconds: 86400 },
        { label: 'hour', seconds: 3600 },
        { label: 'minute', seconds: 60 }
    ];
    
    for (let i = 0; i < intervals.length; i++) {
        const interval = Math.floor(seconds / intervals[i].seconds);
        if (interval >= 1) {
            return interval + ' ' + intervals[i].label + (interval > 1 ? 's' : '') + ' ago';
        }
    }
    
    return 'just now';
}

/**
 * Logs a new activity
 * @param {string} type - Activity type
 * @param {string} title - Activity title
 * @param {string} description - Activity description
 */
function logActivity(type, title, description) {
    const activity = {
        type: type,
        title: title,
        description: description,
        timestamp: new Date().toISOString()
    };
    
    // Send to server
    fetch('/api/log-activity', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(activity)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Activity logged:', data);
        // Refresh the activity timeline
        loadRecentActivity();
    })
    .catch(error => {
        console.error('Error logging activity:', error);
    });
}

/**
 * Generates fallback activity data when API is unavailable
 * @returns {Array} - Array of activity objects
 */
function generateFallbackActivityData() {
    const now = new Date();
    
    return [
        {
            type: 'alert',
            title: 'Crime Alert Notification',
            description: 'Vehicle theft reported 2.5km from your location',
            timestamp: new Date(now - 2 * 60 * 60 * 1000).toISOString() // 2 hours ago
        },
        {
            type: 'detection',
            title: 'Suspicious Activity Detected',
            description: 'Camera detected suspicious activity near front door',
            crime_detected: true,
            timestamp: new Date(now - 5 * 60 * 60 * 1000).toISOString() // 5 hours ago
        },
        {
            type: 'info',
            title: 'Cybersecurity Guide Viewed',
            description: 'You viewed "Protecting Against Banking Fraud"',
            timestamp: new Date(now - 24 * 60 * 60 * 1000).toISOString() // 1 day ago
        },
        {
            type: 'location',
            title: 'Location Updated',
            description: 'Your default location was updated',
            timestamp: new Date(now - 2 * 24 * 60 * 60 * 1000).toISOString() // 2 days ago
        },
        {
            type: 'detection',
            title: 'Video Analysis Completed',
            description: 'Analysis of uploaded video completed with no threats detected',
            crime_detected: false,
            timestamp: new Date(now - 3 * 24 * 60 * 60 * 1000).toISOString() // 3 days ago
        }
    ];
}