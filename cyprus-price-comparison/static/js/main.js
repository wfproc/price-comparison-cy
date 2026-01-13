// Main JavaScript file for Cyprus Price Comparison

document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
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
                submitBtn.textContent = 'Loading...';
            }
        });
    });

    // Auto-focus search input on homepage
    const searchInput = document.querySelector('.search-form-hero input');
    if (searchInput) {
        searchInput.focus();
    }

    // Add "external link" indicator to external links
    document.querySelectorAll('a[target="_blank"]').forEach(link => {
        link.setAttribute('rel', 'noopener noreferrer');
    });

    // Price comparison animation on product detail page
    const priceBoxes = document.querySelectorAll('.price-box');
    if (priceBoxes.length > 0) {
        setTimeout(() => {
            priceBoxes.forEach((box, index) => {
                setTimeout(() => {
                    box.style.opacity = '0';
                    box.style.transform = 'translateY(20px)';
                    setTimeout(() => {
                        box.style.transition = 'all 0.5s ease';
                        box.style.opacity = '1';
                        box.style.transform = 'translateY(0)';
                    }, 50);
                }, index * 100);
            });
        }, 100);
    }
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
