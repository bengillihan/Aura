// Dashboard JavaScript functionality

// Global utilities
function showToast(message, type = 'info') {
    // Create toast element
    const toastHtml = `
        <div class="toast align-items-center text-bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    // Add toast to container
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        toastContainer.style.zIndex = '1055';
        document.body.appendChild(toastContainer);
    }
    
    const toastElement = document.createElement('div');
    toastElement.innerHTML = toastHtml;
    toastContainer.appendChild(toastElement.firstElementChild);
    
    // Initialize and show toast
    const toast = new bootstrap.Toast(toastElement.firstElementChild);
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.firstElementChild.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

// Format bytes to human readable format
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Auto-refresh functionality for monitoring pages
function startAutoRefresh(callback, interval = 5000) {
    // Only start auto-refresh on monitoring page
    if (window.location.pathname.includes('monitoring')) {
        setInterval(callback, interval);
    }
}

// Status badge helper
function getStatusBadge(status) {
    const badges = {
        'running': '<i class="fas fa-check-circle me-1"></i>Running',
        'stopped': '<i class="fas fa-stop-circle me-1"></i>Stopped',
        'failed': '<i class="fas fa-exclamation-triangle me-1"></i>Failed',
        'unknown': '<i class="fas fa-question-circle me-1"></i>Unknown',
        'error': '<i class="fas fa-times-circle me-1"></i>Error'
    };
    
    const classes = {
        'running': 'bg-success',
        'stopped': 'bg-secondary', 
        'failed': 'bg-danger',
        'unknown': 'bg-warning',
        'error': 'bg-danger'
    };
    
    return `<span class="badge ${classes[status] || 'bg-secondary'}">${badges[status] || 'Unknown'}</span>`;
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Add any global event listeners here
    console.log('Aura Dashboard initialized');
});

// Error handling for fetch requests
async function fetchWithErrorHandling(url, options = {}) {
    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        console.error('Fetch error:', error);
        showToast(`Network error: ${error.message}`, 'danger');
        return { success: false, error: error.message };
    }
}

// Service management helpers
function updateServiceStatus(serviceName, callback) {
    fetchWithErrorHandling(`/service/status/${serviceName}`)
        .then(result => {
            if (result.success && callback) {
                callback(result.data);
            }
        });
}

// Animation helpers
function addLoadingSpinner(element) {
    element.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Loading...';
}

function removeLoadingSpinner(element, content) {
    element.innerHTML = content;
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+R to refresh (prevent default browser refresh)
    if (e.ctrlKey && e.key === 'r') {
        e.preventDefault();
        window.location.reload();
    }
    
    // Escape to close modals/dropdowns
    if (e.key === 'Escape') {
        // Close any open Bootstrap modals
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
        
        // Close any open dropdowns
        const dropdowns = document.querySelectorAll('.dropdown-menu.show');
        dropdowns.forEach(dropdown => {
            const dropdownInstance = bootstrap.Dropdown.getInstance(dropdown.previousElementSibling);
            if (dropdownInstance) {
                dropdownInstance.hide();
            }
        });
    }
});
