// Main JavaScript for CrediNews

// Global app object
const CrediNews = {
    // Initialize the application
    init() {
        this.setupNavigation();
        this.setupForms();
        this.setupAlerts();
        this.setupTooltips();
    },

    // Setup navigation functionality
    setupNavigation() {
        // Mobile menu toggle
        const mobileToggle = document.querySelector('.mobile-menu-toggle');
        const mobileMenu = document.querySelector('.mobile-nav');
        
        if (mobileToggle && mobileMenu) {
            mobileToggle.addEventListener('click', () => {
                mobileMenu.classList.toggle('active');
            });
        }

        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (mobileMenu && !mobileMenu.contains(e.target) && !mobileToggle.contains(e.target)) {
                mobileMenu.classList.remove('active');
            }
        });
    },

    // Setup form enhancements
    setupForms() {
        // Auto-dismiss alerts after 5 seconds
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => {
                    alert.remove();
                }, 300);
            }, 5000);
        });

        // Form validation feedback
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const requiredFields = form.querySelectorAll('[required]');
                let isValid = true;

                requiredFields.forEach(field => {
                    if (!field.value.trim()) {
                        field.classList.add('error');
                        isValid = false;
                    } else {
                        field.classList.remove('error');
                    }
                });

                if (!isValid) {
                    e.preventDefault();
                    this.showAlert('Please fill in all required fields.', 'danger');
                }
            });
        });
    },

    // Setup alert system
    setupAlerts() {
        // Create alert container if it doesn't exist
        if (!document.querySelector('.alert-container')) {
            const container = document.createElement('div');
            container.className = 'alert-container';
            document.body.appendChild(container);
        }
    },

    // Show alert message
    showAlert(message, type = 'info') {
        const container = document.querySelector('.alert-container');
        if (!container) return;

        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;

        container.appendChild(alert);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 5000);
    },

    // Setup tooltips
    setupTooltips() {
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        tooltipElements.forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip';
                tooltip.textContent = e.target.getAttribute('data-tooltip');
                document.body.appendChild(tooltip);

                const rect = e.target.getBoundingClientRect();
                tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
                tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
            });

            element.addEventListener('mouseleave', () => {
                const tooltip = document.querySelector('.tooltip');
                if (tooltip) {
                    tooltip.remove();
                }
            });
        });
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    CrediNews.init();
});

// Export for global use
window.CrediNews = CrediNews;