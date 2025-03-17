// Custom JavaScript for Telegram to SMS Forwarder

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Flash message auto-dismiss
    setTimeout(function() {
        var flashMessages = document.querySelectorAll('.alert-dismissible');
        flashMessages.forEach(function(message) {
            var alert = new bootstrap.Alert(message);
            alert.close();
        });
    }, 5000);
    
    // Phone number formatting
    var phoneInput = document.getElementById('phone_number');
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            var input = e.target.value.replace(/\D/g, '');
            if (input.length > 0 && input.charAt(0) !== '+') {
                input = '+' + input;
            }
            e.target.value = input;
        });
    }
    
    // Add fade-in animation to cards
    var cards = document.querySelectorAll('.card');
    cards.forEach(function(card, index) {
        setTimeout(function() {
            card.classList.add('fade-in');
        }, index * 100);
    });
    
    // Check service status button functionality
    var statusButton = document.getElementById('check-status-btn');
    if (statusButton) {
        statusButton.addEventListener('click', checkServiceStatus);
    }
});

// Function to check service status
function checkServiceStatus() {
    var statusButton = document.getElementById('check-status-btn');
    var statusIndicator = document.getElementById('status-indicator');
    var statusText = document.getElementById('status-text');
    var lastChecked = document.getElementById('last-checked');
    
    // Disable button and show loading state
    statusButton.disabled = true;
    statusButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Checking...';
    
    // Make AJAX request to check status
    fetch('/check_status', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        // Update status indicator and text
        statusIndicator.className = 'status-indicator';
        
        if (data.status === 'running') {
            statusIndicator.classList.add('status-running');
            statusText.textContent = 'Running';
            statusText.className = 'text-success';
        } else if (data.status === 'error') {
            statusIndicator.classList.add('status-error');
            statusText.textContent = 'Error';
            statusText.className = 'text-danger';
        } else {
            statusIndicator.classList.add('status-unknown');
            statusText.textContent = 'Unknown';
            statusText.className = 'text-secondary';
        }
        
        // Update last checked time
        var now = new Date();
        lastChecked.textContent = now.toLocaleTimeString();
        
        // Re-enable button
        statusButton.disabled = false;
        statusButton.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Check Status';
    })
    .catch(error => {
        console.error('Error checking status:', error);
        
        // Show error state
        statusIndicator.className = 'status-indicator status-error';
        statusText.textContent = 'Connection Error';
        statusText.className = 'text-danger';
        
        // Update last checked time
        var now = new Date();
        lastChecked.textContent = now.toLocaleTimeString();
        
        // Re-enable button
        statusButton.disabled = false;
        statusButton.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Check Status';
    });
}

// Function to format date and time
function formatDateTime(dateString) {
    var date = new Date(dateString);
    return date.toLocaleString();
}

// Function to confirm logout
function confirmLogout() {
    return confirm('Are you sure you want to log out?');
} 