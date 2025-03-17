// Basic JavaScript for Telegram to SMS Forwarder

document.addEventListener('DOMContentLoaded', function() {
    // Handle status check button
    const statusCheckBtn = document.getElementById('check-status-btn');
    if (statusCheckBtn) {
        statusCheckBtn.addEventListener('click', function() {
            checkServiceStatus();
        });
    }
});

// Function to check service status
function checkServiceStatus() {
    const statusElement = document.getElementById('service-status');
    const statusTextElement = document.getElementById('status-text');
    const statusTimeElement = document.getElementById('status-last-check');
    const checkButton = document.getElementById('check-status-btn');
    
    if (!statusElement || !statusTextElement || !checkButton) {
        return;
    }
    
    // Disable button while checking
    checkButton.disabled = true;
    checkButton.innerHTML = 'Checking...';
    
    fetch('/check_status')
        .then(response => response.json())
        .then(data => {
            // Update status display
            if (data.status === 'running') {
                statusElement.className = 'status-running';
                statusTextElement.innerHTML = 'Running';
            } else if (data.status === 'error') {
                statusElement.className = 'status-error';
                statusTextElement.innerHTML = 'Error: ' + (data.message || 'Unknown error');
            } else {
                statusElement.className = 'status-unknown';
                statusTextElement.innerHTML = 'Unknown';
            }
            
            // Update last checked time
            if (statusTimeElement) {
                const now = new Date();
                statusTimeElement.innerHTML = now.toLocaleString();
            }
        })
        .catch(error => {
            console.error('Error checking status:', error);
            statusElement.className = 'status-error';
            statusTextElement.innerHTML = 'Error checking status';
        })
        .finally(() => {
            // Re-enable button
            checkButton.disabled = false;
            checkButton.innerHTML = 'Check Status';
        });
} 