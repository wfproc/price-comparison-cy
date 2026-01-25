// Main JavaScript file for Cyprus Price Comparison

document.addEventListener('DOMContentLoaded', function() {
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+K or Cmd+K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('.search-input') || document.querySelector('.search-form-hero input');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }

        // Escape to clear/blur search
        if (e.key === 'Escape') {
            const searchInput = document.querySelector('.search-input') || document.querySelector('.search-form-hero input');
            if (searchInput && document.activeElement === searchInput) {
                searchInput.blur();
            }
        }
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add loading state to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span style="display:inline-block;width:14px;height:14px;border:2px solid currentColor;border-top-color:transparent;border-radius:50%;animation:spin 0.6s linear infinite;margin-right:8px;"></span>Searching...';

                // Add spin animation if not present
                if (!document.getElementById('spin-animation')) {
                    const style = document.createElement('style');
                    style.id = 'spin-animation';
                    style.textContent = '@keyframes spin { to { transform: rotate(360deg); } }';
                    document.head.appendChild(style);
                }

                // Reset after 10 seconds if still on page
                setTimeout(() => {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalText;
                    }
                }, 10000);
            }
        });
    });

    // Auto-focus search input on homepage
    const searchInput = document.querySelector('.search-form-hero input') || document.querySelector('.search-input');
    if (searchInput && window.location.pathname === '/') {
        searchInput.focus();
    }

    // Add "external link" indicator to external links
    document.querySelectorAll('a[target="_blank"]').forEach(link => {
        link.setAttribute('rel', 'noopener noreferrer');
    });

    // Animate elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);

    // Observe multiple element types
    document.querySelectorAll('.price-box, .result-card, .deal-card, .stat-card, .step-card, .category-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(el);
    });

    // Enhanced hover effects for store comparison rows
    document.querySelectorAll('.comparison-row').forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(8px)';
        });
        row.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0)';
        });
    });

    // Copy product name on click
    document.querySelectorAll('.product-title').forEach(title => {
        title.style.cursor = 'pointer';
        title.title = 'Click to copy product name';
        title.addEventListener('click', function() {
            const text = this.textContent.trim();
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(text).then(() => {
                    showNotification('Product name copied to clipboard!', 'success');
                }).catch(() => {
                    showNotification('Failed to copy to clipboard', 'error');
                });
            }
        });
    });

    // Notification system
    function showNotification(message, type = 'info') {
        // Remove existing notifications
        const existing = document.querySelector('.notification');
        if (existing) existing.remove();

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <svg class="notification-icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                    ${type === 'success' ? '<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>' : '<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>'}
                </svg>
                <span>${message}</span>
            </div>
        `;

        // Add styles if not already present
        if (!document.getElementById('notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                .notification {
                    position: fixed;
                    top: 80px;
                    right: 20px;
                    padding: 12px 20px;
                    background: var(--surface-elevated);
                    border: 1px solid var(--border);
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                    z-index: 10000;
                    animation: slideIn 0.3s ease;
                    max-width: 400px;
                }
                .notification-content {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    color: var(--text-primary);
                }
                .notification-icon {
                    flex-shrink: 0;
                }
                .notification-success {
                    border-left: 3px solid var(--green-500);
                }
                .notification-success .notification-icon {
                    color: var(--green-500);
                }
                .notification-error {
                    border-left: 3px solid var(--red-500);
                }
                .notification-error .notification-icon {
                    color: var(--red-500);
                }
                @keyframes slideIn {
                    from {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
                @keyframes slideOut {
                    from {
                        transform: translateX(0);
                        opacity: 1;
                    }
                    to {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(notification);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Make showNotification globally available
    window.showNotification = showNotification;

    // Add stagger effect to cards
    document.querySelectorAll('.result-card, .deal-card, .stat-card').forEach((card, index) => {
        card.style.transitionDelay = `${index * 0.05}s`;
    });

    // Enhance search input with visual feedback
    const searchForms = document.querySelectorAll('.search-form, .search-form-hero');
    searchForms.forEach(form => {
        const input = form.querySelector('input[type="text"]');
        if (input) {
            input.addEventListener('input', function() {
                if (this.value.length > 0) {
                    this.classList.add('has-value');
                } else {
                    this.classList.remove('has-value');
                }
            });
        }
    });

    // Popular tag click handler
    document.querySelectorAll('.popular-tag').forEach(tag => {
        tag.addEventListener('click', function() {
            const searchInput = document.querySelector('.search-form-hero input') || document.querySelector('.search-input');
            if (searchInput) {
                searchInput.value = this.textContent.trim();
                searchInput.classList.add('has-value');
                // Optionally trigger search
                const form = searchInput.closest('form');
                if (form) {
                    form.submit();
                }
            }
        });
    });
});

// Format currency
function formatCurrency(amount) {
    return '€' + parseFloat(amount).toFixed(2);
}

// Calculate savings percentage
function calculateSavings(original, current) {
    if (!original || !current) return 0;
    return ((original - current) / original * 100).toFixed(1);
}
