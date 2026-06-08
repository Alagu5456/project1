// Main JavaScript functionality for the marketplace

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all JavaScript functionality
    initializeImagePreview();
    initializeSearchFilters();
    initializeFormValidation();
    initializeNotifications();
    initializePriceFormatting();
});

// Image preview functionality for product forms
function initializeImagePreview() {
    const imageInput = document.getElementById('image');
    const imagePreview = document.getElementById('image-preview');
    
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    if (imagePreview) {
                        imagePreview.innerHTML = `
                            <img src="${e.target.result}" alt="Preview" style="max-width: 200px; max-height: 200px; border-radius: 8px; margin-top: 10px;">
                        `;
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }
}

// Search filters functionality
function initializeSearchFilters() {
    const searchForm = document.getElementById('search-form');
    const categoryFilter = document.getElementById('category');
    const priceMinFilter = document.getElementById('min_price');
    const priceMaxFilter = document.getElementById('max_price');
    
    if (searchForm) {
        // Auto-submit form when filters change
        [categoryFilter, priceMinFilter, priceMaxFilter].forEach(filter => {
            if (filter) {
                filter.addEventListener('change', function() {
                    searchForm.submit();
                });
            }
        });
    }
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Password confirmation validation
    const passwordField = document.getElementById('password');
    const confirmPasswordField = document.getElementById('confirm_password');
    
    if (passwordField && confirmPasswordField) {
        confirmPasswordField.addEventListener('input', function() {
            if (passwordField.value !== confirmPasswordField.value) {
                confirmPasswordField.setCustomValidity('Passwords do not match');
            } else {
                confirmPasswordField.setCustomValidity('');
            }
        });
    }
}

// Notification system
function initializeNotifications() {
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        // Auto-dismiss alerts after 5 seconds
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 5000);
        
        // Add close button functionality
        const closeBtn = alert.querySelector('.close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                alert.style.opacity = '0';
                setTimeout(() => {
                    alert.remove();
                }, 300);
            });
        }
    });
}

// Price formatting
function initializePriceFormatting() {
    const priceInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
    
    priceInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const value = parseFloat(this.value);
            if (!isNaN(value)) {
                this.value = value.toFixed(2);
            }
        });
    });
}

// Utility functions
function formatPrice(price) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(price);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
        return 'Today';
    } else if (diffDays === 2) {
        return 'Yesterday';
    } else if (diffDays <= 7) {
        return `${diffDays - 1} days ago`;
    } else {
        return date.toLocaleDateString('en-IN');
    }
}

// Confirmation dialogs
function confirmDelete(message = 'Are you sure you want to delete this item?') {
    return confirm(message);
}

// Image loading error handling
function handleImageError(img) {
    img.style.display = 'none';
    const placeholder = img.nextElementSibling;
    if (placeholder && placeholder.classList.contains('image-placeholder')) {
        placeholder.style.display = 'flex';
    }
}

// Search functionality
function performSearch() {
    const searchQuery = document.getElementById('search-query').value;
    const category = document.getElementById('category-filter').value;
    const location = document.getElementById('location-filter').value;
    
    let searchParams = new URLSearchParams();
    
    if (searchQuery) searchParams.append('query', searchQuery);
    if (category) searchParams.append('category', category);
    if (location) searchParams.append('location', location);
    
    window.location.href = `/search?${searchParams.toString()}`;
}

// Mobile menu toggle
function toggleMobileMenu() {
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenu) {
        mobileMenu.classList.toggle('show');
    }
}

// Lazy loading for images
function initializeLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
    } else {
        // Fallback for older browsers
        images.forEach(img => {
            img.src = img.dataset.src;
            img.classList.remove('lazy');
        });
    }
}

// Initialize lazy loading when page loads
window.addEventListener('load', initializeLazyLoading);
