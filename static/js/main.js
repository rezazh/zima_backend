// اسکریپت‌های عمومی سایت

document.addEventListener('DOMContentLoaded', function() {
    // نمایش و مخفی کردن منوی موبایل
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            document.body.classList.toggle('mobile-menu-open');
        });
    }

    // اضافه کردن کلاس active به لینک فعال منو
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        }
    });

    // نمایش پیام‌های فلش با تأخیر
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.add('fade-out');
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });
});

// تابع افزایش تعداد محصول در صفحه جزئیات محصول
function incrementQuantity() {
    const quantityInput = document.getElementById('quantity');
    if (quantityInput) {
        const max = parseInt(quantityInput.getAttribute('max') || 99);
        const currentValue = parseInt(quantityInput.value);
        if (currentValue < max) {
            quantityInput.value = currentValue + 1;
        }
    }
}

// تابع کاهش تعداد محصول در صفحه جزئیات محصول
function decrementQuantity() {
    const quantityInput = document.getElementById('quantity');
    if (quantityInput) {
        const currentValue = parseInt(quantityInput.value);
        if (currentValue > 1) {
            quantityInput.value = currentValue - 1;
        }
    }
}

// تابع تغییر تصویر اصلی در صفحه جزئیات محصول
function changeMainImage(imageUrl) {
    const mainImage = document.getElementById('main-product-image');
    if (mainImage) {
        mainImage.src = imageUrl;
    }
}