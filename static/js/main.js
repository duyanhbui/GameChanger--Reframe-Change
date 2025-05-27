// Main JavaScript file for Change Management Assessment

document.addEventListener('DOMContentLoaded', function() {
    // Initialize assessment form if present
    if (document.querySelector('.question-radio')) {
        initializeAssessmentForm();
    }
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize smooth scrolling
    initializeSmoothScrolling();
});

/**
 * Initialize assessment form functionality
 */
function initializeAssessmentForm() {
    const questionRadios = document.querySelectorAll('.question-radio');
    const submitBtn = document.getElementById('submitBtn');
    const progressBar = document.getElementById('progressBar');
    
    if (!questionRadios.length || !submitBtn || !progressBar) return;
    
    // Track progress and enable submit button
    function updateProgress() {
        const answeredQuestions = new Set();
        
        questionRadios.forEach(radio => {
            if (radio.checked) {
                answeredQuestions.add(radio.dataset.question);
            }
        });
        
        const progress = (answeredQuestions.size / 3) * 100;
        progressBar.style.width = progress + '%';
        
        // Enable submit button only when all questions are answered
        if (answeredQuestions.size === 3) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i data-feather="check-circle" class="me-2"></i>Get My Results';
            feather.replace(); // Re-render feather icons
        } else {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i data-feather="lock" class="me-2"></i>Answer All Questions First';
            feather.replace(); // Re-render feather icons
        }
    }
    
    // Add event listeners to all radio buttons
    questionRadios.forEach(radio => {
        radio.addEventListener('change', updateProgress);
    });
    
    // Initial progress check
    updateProgress();
    
    // Form submission handling
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            // Add loading state
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
            submitBtn.disabled = true;
        });
    }
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize smooth scrolling for anchor links
 */
function initializeSmoothScrolling() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Print results functionality
 */
function printResults() {
    // Hide unnecessary elements before printing
    const elementsToHide = document.querySelectorAll('.btn-group, .navbar, footer');
    elementsToHide.forEach(el => el.style.display = 'none');
    
    // Trigger print
    window.print();
    
    // Restore elements after printing
    setTimeout(() => {
        elementsToHide.forEach(el => el.style.display = '');
    }, 1000);
}

/**
 * Share results functionality
 */
function shareResults() {
    const url = window.location.href;
    const title = document.title;
    
    // Try to use Web Share API if available
    if (navigator.share) {
        navigator.share({
            title: title,
            url: url,
            text: 'Check out my change management assessment results!'
        }).catch(err => {
            console.log('Error sharing:', err);
            fallbackShare(url);
        });
    } else {
        fallbackShare(url);
    }
}

/**
 * Fallback share functionality
 */
function fallbackShare(url) {
    // Copy URL to clipboard
    if (navigator.clipboard) {
        navigator.clipboard.writeText(url).then(() => {
            showToast('Link copied to clipboard!', 'success');
        }).catch(() => {
            showShareModal(url);
        });
    } else {
        showShareModal(url);
    }
}

/**
 * Show share modal with options
 */
function showShareModal(url) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Share Your Results</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>Copy this link to share your results:</p>
                    <div class="input-group">
                        <input type="text" class="form-control" value="${url}" readonly>
                        <button class="btn btn-outline-secondary" onclick="copyToClipboard('${url}')">Copy</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
    
    // Clean up modal after it's hidden
    modal.addEventListener('hidden.bs.modal', () => {
        document.body.removeChild(modal);
    });
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    
    try {
        document.execCommand('copy');
        showToast('Link copied to clipboard!', 'success');
    } catch (err) {
        showToast('Failed to copy link', 'error');
    }
    
    document.body.removeChild(textArea);
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = getOrCreateToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bootstrapToast = new bootstrap.Toast(toast);
    bootstrapToast.show();
    
    // Clean up toast after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toastContainer.removeChild(toast);
    });
}

/**
 * Get or create toast container
 */
function getOrCreateToastContainer() {
    let container = document.querySelector('.toast-container');
    
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    return container;
}

/**
 * Animate elements on scroll
 */
function initializeScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe cards and sections
    const elementsToAnimate = document.querySelectorAll('.card, .question-section');
    elementsToAnimate.forEach(el => {
        el.classList.add('animate-ready');
        observer.observe(el);
    });
}

/**
 * Handle form validation styling
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
    });
}

// Initialize additional features
document.addEventListener('DOMContentLoaded', function() {
    initializeScrollAnimations();
    initializeFormValidation();
});
