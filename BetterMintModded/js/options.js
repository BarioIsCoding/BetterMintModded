"use strict";

// BetterMint Modded - Simplified Options Handler
// All settings are now managed server-side

// Simple status indicator
function updateStatusIndicator() {
    const indicator = document.querySelector('.status-indicator');
    if (indicator) {
        // Try to connect to server to check status
        fetch('http://localhost:8000/health')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'healthy') {
                    indicator.style.background = '#69923e';
                    indicator.style.animation = 'pulse 2s infinite';
                } else {
                    indicator.style.background = '#ff4444';
                    indicator.style.animation = 'pulse 1s infinite';
                }
            })
            .catch(error => {
                indicator.style.background = '#ff4444';
                indicator.style.animation = 'pulse 1s infinite';
            });
    }
}

// Initialize popup
window.onload = function() {
    console.log('BetterMint Modded popup loaded');
    
    // Update server status
    updateStatusIndicator();
    
    // Check status every 5 seconds
    setInterval(updateStatusIndicator, 5000);
    
    // Add click handler to open server GUI if available
    document.addEventListener('click', function(e) {
        if (e.target.closest('.server-info')) {
            // Try to open server interface
            window.open('http://localhost:8000', '_blank');
        }
    });
    
    // Animate elements on load
    setTimeout(() => {
        document.body.classList.add('loaded');
    }, 100);
};