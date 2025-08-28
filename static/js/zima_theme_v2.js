// static/js/zima_theme_v2.js
document.addEventListener('DOMContentLoaded', () => {
    // Romantic Loading Animation
    window.addEventListener('load', () => {
        setTimeout(() => {
            const loader = document.getElementById('loader');
            if (loader) {
                loader.classList.add('hidden');
            }
        }, 1000); // 2 ثانیه
    });

    // Elegant Custom Cursor System
    const cursor = document.getElementById('cursor');
    const cursorDot = document.getElementById('cursorDot');
    if (cursor && cursorDot) {
        let mouseX = 0, mouseY = 0;
        let cursorX = 0, cursorY = 0;
        document.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;

            // Create sparkle effect randomly (from home page template) - only for home page
            // if (Math.random() > 0.95 && document.body.classList.contains('home-page')) { // فرض بر اینکه صفحه اصلی کلاس 'home-page' دارد
            //     createSparkle(e.clientX, e.clientY);
            // }
        });

        function animateCursor() {
            cursorX += (mouseX - cursorX) * 0.1;
            cursorY += (mouseY - cursorY) * 0.1;

            cursor.style.left = cursorX + 'px';
            cursor.style.top = cursorY + 'px';
            cursorDot.style.left = mouseX + 'px';
            cursorDot.style.top = mouseY + 'px';

            requestAnimationFrame(animateCursor);
        }
        animateCursor();
        // Hover Effects for Cursor
        document.querySelectorAll('a, button, .product-card, .collection-card, .size-btn, .color-option, .material-tag, .page-btn, .social-link, .btn, .nav-icon, .filter-header').forEach(el => {
            el.addEventListener('mouseenter', () => {
                cursor.classList.add('hover'); // نام کلاس به hover تغییر یافت
            });

            el.addEventListener('mouseleave', () => {
                cursor.classList.remove('hover'); // نام کلاس به hover تغییر یافت
            });
        });
    }

    // Sparkle Effect (from home page template)
    function createSparkle(x, y) {
        const sparkle = document.createElement('div');
        sparkle.className = 'sparkle';
        sparkle.style.left = x + 'px';
        sparkle.style.top = y + 'px';
        document.body.appendChild(sparkle);

        setTimeout(() => {
            sparkle.remove();
        }, 1000);
    }
    // Navbar Scroll Effect
    window.addEventListener('scroll', () => {
        const navbar = document.getElementById('navbar');
        if (navbar) {
            if (window.scrollY > 100) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }
    });

    // Fade In Animation (Intersection Observer)
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px' // شروع زودتر انیمیشن
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);
    document.querySelectorAll('.fade-in').forEach(el => {
        observer.observe(el);
    });

    // Heart Animation on Product Favorite (Moved from home page and product list)
    // This function will be called directly in product_list.html and home.html
    window.toggleWishlist = function(button, productId) {
        const icon = button.querySelector('i');
        const isActive = icon.classList.contains('fas');

        // Simulate API call or actual AJAX request
        showLoading();
        fetch('/products/toggle-wishlist/', { //  مسیر واقعی در urls.py شما
            method: 'POST',
            headers: {                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') // Function to get CSRF token
            },
            body: JSON.stringify({ product_id: productId, action: isActive ? 'remove' : 'add' })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {                if (isActive) {
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                    button.classList.remove('active'); // اضافه شده برای حذف کلاس active
                    showToast('محصول از علاقه‌مندی‌ها حذف شد', 'heart-broken');
                } else {
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                    button.classList.add('active'); // اضافه شده برای افزودن کلاس active
                    showToast('محصول به علاقه‌مندی‌ها اضافه شد', 'heart');
                }
                // Optional: Update favorite count
            } else {
                showToast(data.error || 'خطا در تغییر علاقه‌مندی‌ها', 'exclamation-triangle');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            hideLoading();
            showToast('خطا در ارتباط با سرور', 'times-circle');
        });

        // Create floating heart effect (visual feedback)
        createFloatingHeart(button.getBoundingClientRect().left + button.offsetWidth / 2, button.getBoundingClientRect().top + button.offsetHeight / 2);
    };

    function createFloatingHeart(x, y) {
        const heart = document.createElement('div');
        heart.innerHTML = '♥';
        heart.style.cssText = `
            position: fixed;
            left: ${x}px;
            top: ${y}px;
            color: var(--primary-color);
            font-size: 20px;
            pointer-events: none;
            z-index: 1000;
            animation: floatingHeart 2s ease-out forwards;
        `;
        document.body.appendChild(heart);
        setTimeout(() => heart.remove(), 2000);
    }
    // Add floating heart animation style (directly to head)
    if (!document.getElementById('floatingHeartAnimStyle')) {
        const style = document.createElement('style');
        style.id = 'floatingHeartAnimStyle';
        style.textContent = `
        @keyframes floatingHeart {
            0% { opacity: 1; transform: translateY(0) scale(1); }
            100% { opacity: 0; transform: translateY(-100px) scale(1.5); }
        }
        `;
        document.head.appendChild(style);    }

    // Add to Cart Logic (Unified for all product cards, from home and product list templates)
    window.addToCart = function(productId, quantity = 1, colorId = null, sizeId = null, inventoryId = null) {
        showLoading();

        fetch('/cart/add/', { // مطمئن شوید این URL به درستی تعریف شده است
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: quantity,                color_id: colorId,
                size_id: sizeId,
                inventory_id: inventoryId
            })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                showToast('محصول به سبد خرید اضافه شد.', 'check');
                updateCartBadge(data.cart_items_count); // Update cart count in header
                if (data.redirect) {
                    // Redirect if required (e.g., if user not logged in for certain actions)
                    window.location.href = data.redirect;
                }
            } else {
                showToast(data.error || 'خطا در افزودن محصول به سبد خرید.', 'exclamation-triangle');
                if (data.redirect) {
                    window.location.href = data.redirect;
                }
            }
        })
        .catch(error => {
            console.error('Error adding to cart:', error);
            hideLoading();
            showToast('خطا در ارتباط با سرور.', 'times-circle');
        });
    };

    // Update Cart Badge in Navbar
    window.updateCartBadge = function(count) {
        const cartBadge = document.getElementById('cart-items-count');
        if (cartBadge) {
            cartBadge.textContent = count;
            cartBadge.style.transform = 'scale(1.3)';
            setTimeout(() => {
                cartBadge.style.transform = 'scale(1)';
            }, 200);
        }
    };

    // Quick View Modal Logic (For product_list.html and related pages)
    window.openQuickView = function(productId) {
        showLoading();
        fetch(`/products/${productId}/quick-view/`) // URL برای دریافت جزئیات محصول با AJAX
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.text();
            })
            .then(html => {
                hideLoading();
                document.getElementById('quickViewModalContent').innerHTML = html; // محتوای Quick View در این ID قرار می‌گیرد
                const modal = document.getElementById('quickViewModal');
                modal.classList.add('active');
                document.body.style.overflow = 'hidden'; // جلوگیری از اسکرول صفحه
            })
            .catch(error => {
                console.error('Error fetching quick view:', error);
                hideLoading();
                showToast('خطا در بارگذاری جزئیات محصول.', 'times-circle');
            });
    };

    window.closeQuickView = function() {
        const modal = document.getElementById('quickViewModal');
        modal.classList.remove('active');
        document.body.style.overflow = 'auto'; // بازگرداندن اسکرول صفحه
        document.getElementById('quickViewModalContent').innerHTML = ''; // پاک کردن محتوا
    };

    // Change Image in Modal (For Quick View)
    window.changeImage = function(thumbnail) {
        const mainImage = document.getElementById('mainImageQv'); // ID تغییر یافته
        mainImage.src = thumbnail.src;

        document.querySelectorAll('.thumbnail-qv').forEach(thumb => { // کلاس تغییر یافته
            thumb.classList.remove('active');
        });
        thumbnail.classList.add('active');
    };

    // Quantity Selector in Modal (For Quick View)
    window.increaseQuantity = function() {
        const input = document.getElementById('quantityInputQv'); // ID تغییر یافته
        let value = parseInt(input.value);
        const max = parseInt(input.getAttribute('max'));
        if (value < max) {
            input.value = value + 1;
        }
    };
    window.decreaseQuantity = function() {
        const input = document.getElementById('quantityInputQv'); // ID تغییر یافته
        let value = parseInt(input.value);
        if (value > 1) {
            input.value = value - 1;
        }
    };    // Newsletter Form (already moved to base.html, this is just for the JS logic)
    const newsletterForm = document.getElementById('newsletterForm'); // باید در base.html ID داشته باشد
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const input = e.target.querySelector('.newsletter-input');
            const button = e.target.querySelector('.newsletter-submit');
            // Simulate form submission
            showLoading(); // تابع showLoading از همین فایل است
            setTimeout(() => {
                hideLoading(); // تابع hideLoading از همین فایل است
                showToast('با موفقیت عضو خبرنامه شدید!', 'envelope'); // تابع showToast از همین فایل است
                input.value = '';
                button.innerHTML = '<i class="fas fa-heart"></i> ممنون!'; // تغییر متن دکمه
                setTimeout(() => {
                    button.textContent = 'عضویت';
                }, 1500); // بازگرداندن متن دکمه پس از ۱.۵ ثانیه
            }, 1500);

            // در یک پروژه Django واقعی، شما فرم را از طریق fetch یا form.submit() ارسال می‌کنید
            // e.g., this.submit();
        });
    }


    // Testimonials Auto Scroll (from home page template)
    const testimonialSlider = document.querySelector('.testimonials-slider');
    if (testimonialSlider) {
        let testimonialScrollAmount = 0;

        setInterval(() => {
            testimonialScrollAmount += 390; // عرض تقریبی کارت (350px) + gap (40px)
            // اگر به انتهای اسلایدر رسیدیم، به ابتدا برگردیم
            if (testimonialScrollAmount >= testimonialSlider.scrollWidth - testimonialSlider.clientWidth) {
                testimonialScrollAmount = 0;
            }
            testimonialSlider.scrollTo({
                left: testimonialScrollAmount,
                behavior: 'smooth'
            });
        }, 4000); // هر 4 ثانیه
    }

    // Product Image Hover Effect (from home page template)
    document.querySelectorAll('.product-card').forEach(card => {
        const image = card.querySelector('.product-image');
        if (image) { // اطمینان از وجود تصویر
            card.addEventListener('mouseenter', () => {
                image.style.filter = 'brightness(1.1) saturate(1.2)';
            });

            card.addEventListener('mouseleave', () => {
                image.style.filter = '';
            });
        }
    });

    // Filter Toggle in Sidebar (for product pages)
    document.querySelectorAll('.filter-header').forEach(header => {
        header.addEventListener('click', () => {
            const content = header.nextElementSibling;
            const section = header.parentElement;
            section.classList.toggle('collapsed');
            toggle.classList.toggle('active'); // برای چرخش آیکون
            if (section.classList.contains('collapsed')) {
                content.style.maxHeight = '0px';
                content.style.paddingTop = '0px';
                content.style.paddingBottom = '0px';
            } else {
                content.style.maxHeight = content.scrollHeight + "px"; // باز کردن کامل
                content.style.paddingTop = '15px';
                content.style.paddingBottom = '20px';
            }
        });
    });

    // Mobile Filter Toggle (for product pages)
    window.toggleMobileFilter = function() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.toggle('mobile-active');
        }
    };
    window.getColorCode = function(colorName) {
    const colorMap = {
        'سفید': '#FFFFFF', 'مشکی': '#000000', 'خاکستری': '#808080', 'نقره‌ای': '#C0C0C0',
        'قرمز': '#FF0000', 'زرشکی': '#800000', 'صورتی': '#FFC0CB', 'گلبهی': '#FFB6C1',
        'نارنجی': '#FFA500', 'هلویی': '#FFDAB9', 'طلایی': '#FFD700', 'زرد': '#FFFF00', 'لیمویی': '#BFFF00',
        'سبز': '#00FF00', 'سبز لجنی': '#2F4F4F', 'سبز یشمی': '#00A86B', 'سبز زیتونی': '#808000',
        'آبی': '#0000FF', 'آبی آسمانی': '#87CEEB', 'آبی نفتی': '#000080', 'فیروزه‌ای': '#40E0D0',
        'بنفش': '#800080', 'یاسی': '#DDA0DD', 'ارغوانی': '#9370DB',
        'قهوه‌ای': '#A52A2A', 'کرم': '#FFFDD0', 'بژ': '#F5F5DC', 'شکلاتی': '#5C4033', 'عنابی': '#722F37',
        'مسی': '#B87333', 'برنزی': '#CD7F32', 'سرمه‌ای': '#191970', 'کالباسی': '#E34234', 'نباتی': '#FAEBD7', 'آجری': '#B22222',
        'آبی_روشن': '#ADD8E6', 'طوسی': '#808080', 'جگری': '#8B0000', 'آبی_کاربنی': '#003366', 'بنفش_روشن': '#E0B4D6',
        'زیتونی': '#808000', 'آلبالویی': '#8B0000', 'کاهویی': '#ADFF2F', 'آبی_ملایم': '#6495ED', 'بژ_روشن': '#F5F5DC',
        'خاکی': '#C2B280', 'سیلور': '#C0C0C0', 'نارنجی_سیر': '#FF8C00', 'آبی_نفتی_تیره': '#000080', 'بنفش_پررنگ': '#8A2BE2',
        'زرد_طلایی': '#FFD700', 'ارغوانی_روشن': '#D8BFD8', 'یشمی_روشن': '#7FFFD4', 'آبی_دریایی': '#000080', 'براق': '#E0E0E0',
    };
    return colorMap[colorName] || '#CCCCCC';
};
    // Close modal on outside click (for Quick View)
    const quickViewModal = document.getElementById('quickViewModal');
    if (quickViewModal) {
        quickViewModal.addEventListener('click', function(e) {
            if (e.target === this) {                closeQuickView();
            }
        });
    }

    // Close mobile filter on outside click
    document.addEventListener('click', function(e) {
        const sidebar = document.getElementById('sidebar');
        const toggle = document.querySelector('.mobile-filter-toggle'); // این دکمه را باید در product_list.html ایجاد کنید

        if (sidebar && toggle && sidebar.classList.contains('mobile-active') &&
            !sidebar.contains(e.target) &&
            !toggle.contains(e.target)) {
            sidebar.classList.remove('mobile-active');
        }
    });


    // Global Toast Notification (Accessible from other JS files)
    window.showToast = function(message, icon = 'check') {
        const toast = document.getElementById('toast');
        if (!toast) {
            console.error('Toast element not found!');
            return;
        }
        const toastIcon = toast.querySelector('.toast-icon i');
        const toastMessage = toast.querySelector('.toast-message');

        if (toastIcon) toastIcon.className = `fas fa-${icon}`;
        if (toastMessage) toastMessage.textContent = message;

        toast.classList.add('show');

        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    };

    // Global Loading Spinner (Accessible from other JS files)
    window.showLoading = function() {
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) {
            spinner.style.display = 'block';
        }
    };
    window.hideLoading = function() {
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) {
            spinner.style.display = 'none';
        }
    };

    // Django Messages Auto-Hide (if not already handled by main.js)
    const djangoMessagesContainer = document.querySelector('.django-messages');
    if (djangoMessagesContainer) {
        const alerts = djangoMessagesContainer.querySelectorAll('.alert');
        alerts.forEach(alert => {
            setTimeout(() => {
                // Add fade-out class (if you have one in your CSS)
                alert.style.opacity = '0';
                alert.style.transition = 'opacity 0.5s ease';
                setTimeout(() => {
                    alert.remove();
                }, 500);
            }, 5000); // Hide after 5 seconds
        });
    }

    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    document.querySelectorAll('.filter-header').forEach(header => {
        header.addEventListener('click', () => {
            const content = header.nextElementSibling;

            header.classList.toggle('active');

            if (content.style.maxHeight && content.style.maxHeight !== '0px') {
                // اگر باز است، آن را ببند
                content.style.maxHeight = '0px';
            } else {
                // اگر بسته است، آن را باز کن
                // ارتفاع را بر اساس محتوای واقعی داخل آن تنظیم کن
                content.style.maxHeight = content.scrollHeight + "px";
            }
        });
    });
    window.addEventListener('resize', () => {
        document.querySelectorAll('.filter-content').forEach(content => {
            if (content.style.maxHeight && content.style.maxHeight !== '0px') {
                content.style.maxHeight = content.scrollHeight + "px";
            }
        });
    });
    // Console Branding (از تمپلیت صفحه اصلی) - فونت تغییر یافت به Playfair Display
    console.log(`
████████╗██╗███╗ ███╗ █████╗
╚══██╔══╝██║████╗ ████║██╔══██╗
██║ ██║██╔████╔██║███████║
██║ ██║██║╚██╔╝██║██╔══██║
██║ ██║██║ ╚═╝ ██║██║ ██║
╚═╝ ╚═╝╚═╝ ╚═╝╚═╝ ╚═╝

وبسایت زیما - جایی که زیبایی زندگی می‌کند
`);
});