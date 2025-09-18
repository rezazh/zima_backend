// static/js/zima_theme_v2.js

// ✅ متغیرهای سراسری Quick View
let productDataQv = {};
let inventoryMappingQv = {};
let selectedColorQv = null;
let selectedSizeQv = null;
let currentStockQv = 0;

// ✅ توابع سراسری Quick View که باید قبل از DOMContentLoaded باشند
window.increaseQuantityQv = function() {
    const input = document.getElementById('quantityInputQv');
    if (input && parseInt(input.value) < parseInt(input.max)) {
        input.value = parseInt(input.value) + 1;
    }
};

window.decreaseQuantityQv = function() {
    const input = document.getElementById('quantityInputQv');
    if (input && parseInt(input.value) > 1) {
        input.value = parseInt(input.value) - 1;
    }
};

window.changeImageQv = function(thumbnail) {
    const mainImage = document.getElementById('mainImageQv');
    if (mainImage && thumbnail) {
        mainImage.src = thumbnail.src;

        document.querySelectorAll('.thumbnail-qv').forEach(thumb => {
            thumb.classList.remove('active');
        });

        thumbnail.classList.add('active');
    }
};

window.closeQuickViewModal = function() {
    const modal = document.getElementById('quickViewModal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = 'auto';
    }
};

// ✅ تابع اصلی initialization Quick View
window.initQuickViewModalContent = function(dataFromAjax) {
    console.log('🔄 initQuickViewModalContent called with data:', dataFromAjax);

    // تنظیم متغیرهای سراسری
    productDataQv = dataFromAjax;
    inventoryMappingQv = dataFromAjax.inventoryMapping || {};
    currentStockQv = productDataQv.stock || 0;

    // ریست کردن انتخاب‌ها
    selectedColorQv = null;
    selectedSizeQv = null;

    console.log('📊 Inventory Mapping:', inventoryMappingQv);

    // رندر کردن گزینه‌ها
    renderQuickViewOptions();

    // نمایش یا مخفی کردن بخش‌ها
    toggleQuickViewSections();

    // همه گزینه‌ها در ابتدا فعال هستند
    resetAllOptionsAvailability();
    updateQuickViewAddToCartButton();

    console.log('✅ Quick View initialized successfully');
};

// ✅ تابع رندر کردن گزینه‌های رنگ و سایز
function renderQuickViewOptions() {
    console.log('🎨 Rendering Quick View options...');

    const colorContainer = document.getElementById('modalColorOptionsQv');
    const sizeContainer = document.getElementById('modalSizeOptionsQv');

    if (!colorContainer || !sizeContainer) {
        console.error('❌ Quick View containers not found');
        return;
    }

    // پاک کردن محتوای قبلی
    colorContainer.innerHTML = '';
    sizeContainer.innerHTML = '';

    // رندر کردن رنگ‌ها
    if (productDataQv.availableColors && productDataQv.availableColors.length > 0) {
        productDataQv.availableColors.forEach(color => {
            const colorElement = document.createElement('label');
            colorElement.className = 'color-option-qv';
            colorElement.setAttribute('data-color-id', color.id);
            colorElement.setAttribute('data-color-name', color.name);
            colorElement.setAttribute('title', color.name);

            const colorCode = color.hex_code || '#CCCCCC';
            colorElement.style.backgroundColor = colorCode;

            // border برای رنگ‌های روشن
            if (colorCode.toUpperCase() === '#FFFFFF') {
                colorElement.style.border = '2px solid #ddd';
            }

            colorElement.innerHTML = `<input type="radio" name="colorQv" value="${color.id}" style="display:none;">`;

            colorElement.addEventListener('click', function(e) {
                e.preventDefault();
                if (!this.classList.contains('disabled')) {
                    selectQuickViewColor(color.id, color.name);
                }
            });

            colorContainer.appendChild(colorElement);
        });
    }

    // رندر کردن سایزها
    if (productDataQv.availableSizes && productDataQv.availableSizes.length > 0) {
        productDataQv.availableSizes.forEach(size => {
            const sizeElement = document.createElement('label');
            sizeElement.className = 'size-option-qv';
            sizeElement.setAttribute('data-size-id', size.id);
            sizeElement.setAttribute('data-size-name', size.name);
            sizeElement.innerHTML = `
                <input type="radio" name="sizeQv" value="${size.id}" style="display:none;">
                <span>${size.name}</span>
            `;

            sizeElement.addEventListener('click', function(e) {
                e.preventDefault();
                if (!this.classList.contains('disabled')) {
                    selectQuickViewSize(size.id, size.name);
                }
            });

            sizeContainer.appendChild(sizeElement);
        });
    }
}

// ✅ تابع انتخاب رنگ
function selectQuickViewColor(colorId, colorName) {
    console.log(`🎨 Selecting color: ${colorName} (${colorId})`);

    // حذف انتخاب قبلی رنگ
    document.querySelectorAll('.color-option-qv').forEach(el => {
        el.classList.remove('active');
    });

    // اضافه کردن active به رنگ انتخابی
    const selectedColorElement = document.querySelector(`[data-color-id="${colorId}"]`);
    if (selectedColorElement) {
        selectedColorElement.classList.add('active');
    }

    // تنظیم متغیر
    selectedColorQv = colorId;

    // به‌روزرسانی نام رنگ
    const colorNameElement = document.getElementById('selectedColorNameQv');
    if (colorNameElement) {
        colorNameElement.textContent = colorName;
    }

    // اگر سایزی انتخاب شده بود، بررسی کن آیا با رنگ جدید سازگار است
    if (selectedSizeQv) {
        const isCompatible = checkColorSizeCompatibility(colorId, selectedSizeQv);
        if (!isCompatible) {
            deselectSize();
        }
    }

    // فعال کردن مجدد همه رنگ‌ها
    enableAllColors();

    // به‌روزرسانی سایزهای قابل انتخاب بر اساس رنگ
    updateSizeAvailabilityBasedOnColor(colorId);

    // به‌روزرسانی موجودی و دکمه
    updateQuickViewStock();
    updateQuickViewAddToCartButton();
}

// ✅ تابع انتخاب سایز
function selectQuickViewSize(sizeId, sizeName) {
    console.log(`📏 Selecting size: ${sizeName} (${sizeId})`);

    // حذف انتخاب قبلی سایز
    document.querySelectorAll('.size-option-qv').forEach(el => {
        el.classList.remove('active');
    });

    // اضافه کردن active به سایز انتخابی
    const selectedSizeElement = document.querySelector(`[data-size-id="${sizeId}"]`);
    if (selectedSizeElement) {
        selectedSizeElement.classList.add('active');
    }

    // تنظیم متغیر
    selectedSizeQv = sizeId;

    // به‌روزرسانی نام سایز
    const sizeNameElement = document.getElementById('selectedSizeNameQv');
    if (sizeNameElement) {
        sizeNameElement.textContent = sizeName;
    }

    // اگر رنگی انتخاب شده بود، بررسی کن آیا با سایز جدید سازگار است
    if (selectedColorQv) {
        const isCompatible = checkColorSizeCompatibility(selectedColorQv, sizeId);
        if (!isCompatible) {
            deselectColor();
        }
    }

    // فعال کردن مجدد همه سایزها
    enableAllSizes();

    // به‌روزرسانی رنگ‌های قابل انتخاب بر اساس سایز
    updateColorAvailabilityBasedOnSize(sizeId);

    // به‌روزرسانی موجودی و دکمه
    updateQuickViewStock();
    updateQuickViewAddToCartButton();
}

// ✅ توابع کمکی Quick View
function checkColorSizeCompatibility(colorId, sizeId) {
    const colorKey = colorId.toString();
    const sizeKey = sizeId.toString();

    return inventoryMappingQv[colorKey] &&
           inventoryMappingQv[colorKey][sizeKey] &&
           inventoryMappingQv[colorKey][sizeKey].quantity > 0;
}

function deselectColor() {
    selectedColorQv = null;
    document.querySelectorAll('.color-option-qv').forEach(el => {
        el.classList.remove('active');
    });

    const colorNameElement = document.getElementById('selectedColorNameQv');
    if (colorNameElement) {
        colorNameElement.textContent = 'انتخاب کنید';
    }
}

function deselectSize() {
    selectedSizeQv = null;
    document.querySelectorAll('.size-option-qv').forEach(el => {
        el.classList.remove('active');
    });

    const sizeNameElement = document.getElementById('selectedSizeNameQv');
    if (sizeNameElement) {
        sizeNameElement.textContent = 'انتخاب کنید';
    }
}

function enableAllColors() {
    document.querySelectorAll('.color-option-qv').forEach(el => {
        el.classList.remove('disabled');
        el.style.opacity = '1';
        el.style.pointerEvents = 'auto';
    });
}

function enableAllSizes() {
    document.querySelectorAll('.size-option-qv').forEach(el => {
        el.classList.remove('disabled');
        el.style.opacity = '1';
        el.style.pointerEvents = 'auto';
    });
}

function updateSizeAvailabilityBasedOnColor(colorId) {
    const colorKey = colorId.toString();
    const availableForColor = inventoryMappingQv[colorKey] || {};

    console.log(`📏 Updating sizes for color ${colorId}:`, availableForColor);

    document.querySelectorAll('.size-option-qv').forEach(sizeOption => {
        const sizeId = sizeOption.getAttribute('data-size-id');
        const sizeKey = sizeId.toString();

        const isAvailable = availableForColor[sizeKey] && availableForColor[sizeKey].quantity > 0;

        if (isAvailable) {
            sizeOption.classList.remove('disabled');
            sizeOption.style.opacity = '1';
            sizeOption.style.pointerEvents = 'auto';
        } else {
            sizeOption.classList.add('disabled');
            sizeOption.style.opacity = '0.3';
            sizeOption.style.pointerEvents = 'none';
        }
    });
}

function updateColorAvailabilityBasedOnSize(sizeId) {
    const sizeKey = sizeId.toString();

    console.log(`🎨 Updating colors for size ${sizeId}`);

    document.querySelectorAll('.color-option-qv').forEach(colorOption => {
        const colorId = colorOption.getAttribute('data-color-id');
        const colorKey = colorId.toString();

        const isAvailable = inventoryMappingQv[colorKey] &&
                           inventoryMappingQv[colorKey][sizeKey] &&
                           inventoryMappingQv[colorKey][sizeKey].quantity > 0;

        if (isAvailable) {
            colorOption.classList.remove('disabled');
            colorOption.style.opacity = '1';
            colorOption.style.pointerEvents = 'auto';
        } else {
            colorOption.classList.add('disabled');
            colorOption.style.opacity = '0.3';
            colorOption.style.pointerEvents = 'none';
        }
    });
}

function resetAllOptionsAvailability() {
    enableAllColors();
    enableAllSizes();
}

function updateQuickViewStock() {
    if (!selectedColorQv || !selectedSizeQv) {
        currentStockQv = productDataQv.stock || 0;
        return;
    }

    const colorKey = selectedColorQv.toString();
    const sizeKey = selectedSizeQv.toString();

    if (inventoryMappingQv[colorKey] && inventoryMappingQv[colorKey][sizeKey]) {
        const stock = inventoryMappingQv[colorKey][sizeKey].quantity;
        currentStockQv = stock;

        const quantityInput = document.getElementById('quantityInputQv');
        if (quantityInput) {
            quantityInput.max = stock;
            if (parseInt(quantityInput.value) > stock) {
                quantityInput.value = Math.min(stock, 1);
            }
        }

        console.log(`📦 Updated stock for ${colorKey}-${sizeKey}: ${stock}`);
    } else {
        currentStockQv = 0;
    }
}

function toggleQuickViewSections() {
    const colorSection = document.getElementById('colorOptionGroupQv');
    const sizeSection = document.getElementById('sizeOptionGroupQv');

    if (colorSection) {
        if (productDataQv.availableColors && productDataQv.availableColors.length > 0) {
            colorSection.style.display = 'block';
        } else {
            colorSection.style.display = 'none';
            selectedColorQv = 'null';
        }
    }

    if (sizeSection) {
        if (productDataQv.availableSizes && productDataQv.availableSizes.length > 0) {
            sizeSection.style.display = 'block';
        } else {
            sizeSection.style.display = 'none';
            selectedSizeQv = 'null';
        }
    }
}

function updateQuickViewAddToCartButton() {
    const addButton = document.getElementById('addToCartBtnQv');
    if (!addButton) return;

    const needsColor = productDataQv.availableColors && productDataQv.availableColors.length > 0;
    const needsSize = productDataQv.availableSizes && productDataQv.availableSizes.length > 0;

    const hasRequiredColor = !needsColor || selectedColorQv;
    const hasRequiredSize = !needsSize || selectedSizeQv;

    if (hasRequiredColor && hasRequiredSize && currentStockQv > 0) {
        addButton.disabled = false;
        addButton.classList.remove('disabled');
        addButton.innerHTML = '<i class="fas fa-shopping-bag"></i> افزودن به سبد خرید';
    } else {
        addButton.disabled = true;
        addButton.classList.add('disabled');

        if (needsColor && !selectedColorQv) {
            addButton.innerHTML = '<i class="fas fa-shopping-bag"></i> ابتدا رنگ را انتخاب کنید';
        } else if (needsSize && !selectedSizeQv) {
            addButton.innerHTML = '<i class="fas fa-shopping-bag"></i> ابتدا سایز را انتخاب کنید';
        } else if (currentStockQv <= 0) {
            addButton.innerHTML = '<i class="fas fa-shopping-bag"></i> ناموجود';
        }
    }
}

// ✅ تابع افزودن به سبد خرید از Modal
window.addToCartFromModal = function(productId) {
    console.log('🛒 Adding to cart from modal...');

    const quantity = parseInt(document.getElementById('quantityInputQv').value) || 1;

    // بررسی انتخاب رنگ
    if (productDataQv.availableColors && productDataQv.availableColors.length > 0 && !selectedColorQv) {
        alert('لطفاً رنگ مورد نظر را انتخاب کنید');
        return;
    }

    // بررسی انتخاب سایز
    if (productDataQv.availableSizes && productDataQv.availableSizes.length > 0 && !selectedSizeQv) {
        alert('لطفاً سایز مورد نظر را انتخاب کنید');
        return;
    }

    // بررسی موجودی
    if (currentStockQv <= 0) {
        alert('این محصول موجود نیست');
        return;
    }

    if (quantity > currentStockQv) {
        alert(`تنها ${currentStockQv} عدد از این محصول موجود است`);
        return;
    }

    const cartData = {
        product_id: productId,
        color_id: selectedColorQv || null,
        size_id: selectedSizeQv || null,
        quantity: quantity
    };

    console.log('🛒 Cart data:', cartData);

    // نمایش loading
    const addButton = document.getElementById('addToCartBtnQv');
    const originalText = addButton.innerHTML;
    addButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> در حال افزودن...';
    addButton.disabled = true;

    // ارسال درخواست AJAX
    fetch('/products/add-to-cart/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(cartData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccessMessage(data.message || 'محصول با موفقیت به سبد خرید اضافه شد');

            if (data.cart_items_count) {
                updateCartCount(data.cart_items_count);
            }

            setTimeout(() => {
                closeQuickViewModal();
            }, 1000);
        } else {
            alert(data.error || 'خطا در افزودن به سبد خرید');
        }
    })
    .catch(error => {
        console.error('Error adding to cart:', error);
        alert('خطا در افزودن به سبد خرید');
    })
    .finally(() => {
        addButton.innerHTML = originalText;
        addButton.disabled = false;
    });
};

// ✅ توابع کمکی
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

function showSuccessMessage(message) {
    const toast = document.createElement('div');
    toast.className = 'success-toast';
    toast.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <span>${message}</span>
    `;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #28a745;
        color: white;
        padding: 15px 20px;
        border-radius: 5px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 14px;
        animation: slideInRight 0.3s ease;
        font-family: 'IRANSans', sans-serif;
        direction: rtl;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

function updateCartCount(count) {
    const cartCountElements = document.querySelectorAll('.cart-count, .cart-counter, #cart-count');
    cartCountElements.forEach(element => {
        element.textContent = count;
        if (count > 0) {
            element.style.display = 'inline';
        }
    });
}

// ==================== FAMILY VIDEO FUNCTIONALITY (Global Functions) ====================

let currentFamilyVideo = null;
let familyVideoTimeout = null;

// تابع پخش ویدیو عضو خانواده
window.playFamilyVideo = function(memberType) {
    console.log('🎬 Playing family video for:', memberType);

    // پاک کردن timeout قبلی
    if (familyVideoTimeout) {
        clearTimeout(familyVideoTimeout);
    }

    // متوقف کردن ویدیو قبلی
    if (currentFamilyVideo) {
        currentFamilyVideo.pause();
        currentFamilyVideo.currentTime = 0;
        currentFamilyVideo.classList.remove('playing');
    }

    // مخفی کردن تصویر اصلی
    const mainImage = document.getElementById('familyMainImage');
    if (mainImage) {
        mainImage.classList.remove('active');
    }

    // ✅ تغییر پس‌زمینه محو شده بر اساس نوع عضو خانواده
    const backgroundBlur = document.getElementById('familyBackgroundBlur');
    if (backgroundBlur) {
        const imageMap = {
            'dad': '/static/images/family/men-category.jpg',
            'mom': '/static/images/family/women-category.jpg',
            'boy': '/static/images/family/boys-category.jpg',
            'girl': '/static/images/family/girls-category.jpg'
        };

        const backgroundImage = imageMap[memberType] || '/static/images/family/family-main.jpg';
        backgroundBlur.style.backgroundImage = `url('${backgroundImage}')`;
    }

    // پیدا کردن و پخش ویدیو جدید
    const videoId = memberType + 'Video';
    const video = document.getElementById(videoId);

    if (video) {
        currentFamilyVideo = video;
        video.classList.add('playing');

        // پخش ویدیو
        video.currentTime = 0;
        const playPromise = video.play();

        if (playPromise !== undefined) {
            playPromise.then(() => {
                console.log('✅ Video started playing');

                // متوقف کردن خودکار بعد از 5 ثانیه
                familyVideoTimeout = setTimeout(() => {
                    stopFamilyVideo();
                }, 5000);

            }).catch(error => {
                console.log('❌ Video play failed:', error);
                stopFamilyVideo();
            });
        }

        // اضافه کردن event listener برای پایان ویدیو
        video.onended = function() {
            stopFamilyVideo();
        };
    }
};

// تابع متوقف کردن ویدیو
window.stopFamilyVideo = function() {
    console.log('⏹️ Stopping family video');

    // پاک کردن timeout
    if (familyVideoTimeout) {
        clearTimeout(familyVideoTimeout);
        familyVideoTimeout = null;
    }

    // متوقف کردن ویدیو فعلی
    if (currentFamilyVideo) {
        currentFamilyVideo.pause();
        currentFamilyVideo.currentTime = 0;
        currentFamilyVideo.classList.remove('playing');
        currentFamilyVideo = null;
    }

    // ✅ بازگشت پس‌زمینه به حالت اصلی
    const backgroundBlur = document.getElementById('familyBackgroundBlur');
    if (backgroundBlur) {
        backgroundBlur.style.backgroundImage = "url('/static/images/family/family-main.jpg')";
    }

    // نمایش مجدد تصویر اصلی
    const mainImage = document.getElementById('familyMainImage');
    if (mainImage) {
        setTimeout(() => {
            mainImage.classList.add('active');
        }, 200);
    }
};
// کنترل volume برای تمام ویدیوها (در صورت نیاز)
window.setFamilyVideosVolume = function(volume = 0) {
    const familyVideos = document.querySelectorAll('.family-video');
    familyVideos.forEach(video => {
        video.volume = volume;
    });
};
setFamilyVideosVolume(0); // تنظیم volume در شروع (بدون صدا)

// ==================== END FAMILY VIDEO FUNCTIONALITY (Global Functions) ====================


// ✅ اصلی DOMContentLoaded شروع می‌شود
document.addEventListener('DOMContentLoaded', () => {
    // Romantic Loading Animation
    window.addEventListener('load', () => {
        setTimeout(() => {
            const loader = document.getElementById('loader');
            if (loader) {
                loader.classList.add('hidden');
            }
        }, 1000);
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
        document.querySelectorAll('a, button, .product-card, .collection-card, .size-btn, .color-option, .material-tag, .page-btn, .social-link, .btn, .nav-icon, .filter-header, .family-collection-card').forEach(el => { // ✅ اضافه شدن .family-collection-card
            try {
                el.addEventListener('mouseenter', () => {
                    cursor.classList.add('hover');
                });

                el.addEventListener('mouseleave', () => {
                    cursor.classList.remove('hover');
                });
            } catch (e) {
                console.warn("Could not add event listener to element:", el, e);
            }
        });
    }

    // Sparkle Effect
    window.createSparkle = function(x, y) {
        const sparkle = document.createElement('div');
        sparkle.className = 'sparkle';
        sparkle.style.left = x + 'px';
        sparkle.style.top = y + 'px';
        document.body.appendChild(sparkle);

        setTimeout(() => {
            sparkle.remove();
        }, 1000);
    };

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

    // Fade In Animation
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
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

    // Heart Animation on Product Favorite
    window.toggleWishlist = function(button, productId) {
    const icon = button.querySelector('i');
    const isActive = icon.classList.contains('fas');

    showLoading();
    fetch('/products/toggle-wishlist/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ product_id: productId, action: isActive ? 'remove' : 'add' })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            // ✅ تغییر اینجا: از data.is_favorited برای تعیین وضعیت استفاده کنید
            // و از data.message برای نمایش پیام استفاده کنید.
            if (data.is_favorited) { // اگر حالا مورد علاقه است (یعنی اضافه شده)
                icon.classList.remove('far');
                icon.classList.add('fas');
                button.classList.add('active');
                showToast(data.message || 'محصول به علاقه‌مندی‌ها اضافه شد', 'heart'); // استفاده از data.message
            } else { // اگر حالا مورد علاقه نیست (یعنی حذف شده)
                icon.classList.remove('fas');
                icon.classList.add('far');
                button.classList.remove('active');
                showToast(data.message || 'محصول از علاقه‌مندی‌ها حذف شد', 'heart-broken'); // استفاده از data.message
            }
        } else {
            // ✅ اگر success=false بود، پیام خطا را نمایش دهید.
            showToast(data.message || 'خطا در تغییر علاقه‌مندی‌ها', 'exclamation-triangle');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
        showToast('خطا در ارتباط با سرور', 'times-circle');
    });

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

    // Add floating heart animation style
    if (!document.getElementById('floatingHeartAnimStyle')) {
        const style = document.createElement('style');
        style.id = 'floatingHeartAnimStyle';
        style.textContent = `
        @keyframes floatingHeart {
            0% { opacity: 1; transform: translateY(0) scale(1); }
            100% { opacity: 0; transform: translateY(-100px) scale(1.5); }
        }
        `;
        document.head.appendChild(style);
    }

    // Add to Cart Logic
    window.addToCart = function(productId, quantity = 1, colorId = null, sizeId = null) {
        showLoading();

        fetch('/products/add-to-cart/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: quantity,
                color_id: colorId,
                size_id: sizeId
            })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                showToast('محصول به سبد خرید اضافه شد.', 'check');
                updateCartBadge(data.cart_items_count);
                if (data.redirect) {
                    window.location.href = data.redirect;
                }
            } else {
                showToast(data.message || 'خطا در افزودن محصول به سبد خرید.', 'exclamation-triangle');
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

    // Quick View Modal Logic
    window.openQuickView = function(productId) {
        showLoading();
        fetch(`/products/${productId}/quick-view/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.text();
            })
            .then(html => {
                hideLoading();
                const quickViewModalContentDiv = document.getElementById('quickViewModalContent');
                if (quickViewModalContentDiv) {
                    quickViewModalContentDiv.innerHTML = html;
                    const modal = document.getElementById('quickViewModal');
                    modal.classList.add('active');
                    document.body.style.overflow = 'hidden';

                    const jsonDataElement = quickViewModalContentDiv.querySelector('#quickViewProductJsonData');
                    if (jsonDataElement && jsonDataElement.textContent) {
                        try {
                            const productJsonData = JSON.parse(jsonDataElement.textContent);
                            console.log('Parsed quickViewProductJsonData:', productJsonData);
                            window.initQuickViewModalContent(productJsonData);
                        } catch (e) {
                            console.error("Error parsing quickViewProductJsonData:", e);
                            showToast("خطا در پردازش اطلاعات محصول.", 'exclamation-triangle');
                        }
                    } else {
                        console.error("quickViewProductJsonData element or its content not found in loaded HTML.");
                        showToast("اطلاعات محصول یافت نشد. لطفاً صفحه را رفرش کنید.", 'exclamation-triangle');
                    }

                } else {
                    console.error("quickViewModalContentDiv not found.");
                    showToast("خطا: کانتینر مودال یافت نشد.", 'times-circle');
                }
            })
            .catch(error => {
                console.error('Error fetching quick view:', error);
                hideLoading();
                showToast('خطا در بارگذاری جزئیات محصول.', 'times-circle');
            });
    };

    window.closeQuickView = function() {
        closeQuickViewModal();
        document.getElementById('quickViewModalContent').innerHTML = '';
        // Reset Quick View specific variables
        productDataQv = {};
        inventoryMappingQv = {};
        selectedColorQv = null;
        selectedSizeQv = null;
        currentStockQv = 0;
    };

    // Global Toast Notification
    window.showToast = function(message, icon = 'check') {
        document.querySelectorAll('.toast').forEach(t => t.classList.remove('show'));

        const toast = document.getElementById('toast');
        if (!toast) {
            console.error('Toast element not found!');
            const fallbackToast = document.createElement('div');
            fallbackToast.className = 'toast show';
            fallbackToast.innerHTML = `<div class="toast-icon"><i class="fas fa-${icon}"></i></div><div class="toast-message">${message}</div>`;
            document.body.appendChild(fallbackToast);
            setTimeout(() => {
                fallbackToast.classList.remove('show');
                setTimeout(() => fallbackToast.remove(), 300);
            }, 3000);
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

    // Global Loading Spinner
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

    // Django Messages Auto-Hide
    const djangoMessagesContainer = document.querySelector('.django-messages');
    if (djangoMessagesContainer) {
        const alerts = djangoMessagesContainer.querySelectorAll('.alert');
        alerts.forEach(alert => {
            setTimeout(() => {
                alert.style.opacity = '0';
                alert.style.transition = 'opacity 0.5s ease';
                setTimeout(() => {
                    alert.remove();
                }, 500);
            }, 5000);
        });
    }

    // Filter Toggle in Sidebar
    document.querySelectorAll('.filter-header').forEach(header => {
        try {
            header.addEventListener('click', () => {
                const content = header.nextElementSibling;
                const section = header.parentElement;
                const toggleIcon = header.querySelector('.filter-toggle');

                section.classList.toggle('collapsed');
                if (toggleIcon) {
                    toggleIcon.classList.toggle('active');
                }

                if (section.classList.contains('collapsed')) {
                    content.style.maxHeight = '0px';
                    content.style.paddingTop = '0px';
                    content.style.paddingBottom = '0px';
                } else {
                    content.style.maxHeight = content.scrollHeight + "px";
                    content.style.paddingTop = '15px';
                    content.style.paddingBottom = '20px';
                }
            });
        } catch (e) {
            console.warn("Could not add event listener to filter header:", header, e);
        }
    });

    // Mobile Filter Toggle
    window.toggleMobileFilter = function() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.toggle('mobile-active');
        }
    };

    // Close mobile filter on outside click
    document.addEventListener('click', function(e) {
        const sidebar = document.getElementById('sidebar');
        const toggle = document.querySelector('.mobile-filter-toggle');

        if (sidebar && toggle && sidebar.classList.contains('mobile-active') &&
            !sidebar.contains(e.target) &&
            !toggle.contains(e.target)) {
            sidebar.classList.remove('mobile-active');
        }
    });

    // Handle filter content maxHeight on window resize
    window.addEventListener('resize', () => {
        document.querySelectorAll('.filter-content').forEach(content => {
            if (content.style.maxHeight && content.style.maxHeight !== '0px') {
                content.style.maxHeight = content.scrollHeight + "px";
            }
        });
    });

    // Featured Products Slider Logic
    const sliderContainer = document.querySelector('.slider-container');
    if (sliderContainer) {
        const productsSliderTrack = sliderContainer.querySelector('.products-slider-track');
        const productSlides = productsSliderTrack.querySelectorAll('.product-slide');
        const prevSlideBtn = sliderContainer.querySelector('.prev-slide');
        const nextSlideBtn = sliderContainer.querySelector('.next-slide');
        let currentSlideIndex = 0;

        function updateSlider() {
            productSlides.forEach(slide => {
                slide.classList.remove('active');
            });

            if (productSlides[currentSlideIndex]) {
                productSlides[currentSlideIndex].classList.add('active');
            }

            if (prevSlideBtn) {
                if (currentSlideIndex === 0) {
                    prevSlideBtn.classList.add('disabled');
                } else {
                    prevSlideBtn.classList.remove('disabled');
                }
            }
            if (nextSlideBtn) {
                if (currentSlideIndex === productSlides.length - 1) {
                    nextSlideBtn.classList.add('disabled');
                } else {
                    nextSlideBtn.classList.remove('disabled');
                }
            }
        }

        if (prevSlideBtn) {
            prevSlideBtn.addEventListener('click', () => {
                if (currentSlideIndex > 0) {
                    currentSlideIndex--;
                    updateSlider();
                }
            });
        }

        if (nextSlideBtn) {
            nextSlideBtn.addEventListener('click', () => {
                if (currentSlideIndex < productSlides.length - 1) {
                    currentSlideIndex++;
                    updateSlider();
                }
            });
        }

        updateSlider();
    }

    // Console Branding
    console.log(`
████████╗██╗███╗ ███╗ █████╗
╚══██╔══╝██║████╗ ████║██╔══██╗
██║ ██║██╔████╔██║███████║
██║ ██║██║╚██╔╝██║██╔══██║
██║ ██║██║ ╚═╝ ██║██║ ██║
╚═╝ ╚══╝╚═╝ ╚═╝╚═╝ ╚═╝

وبسایت زیما - جایی که زیبایی زندگی می‌کند
`);

    // === START FAMILY VIDEO INITIALIZATION (MERGED) ===
    const familyShowcaseSection = document.querySelector('.family-showcase');

    if (familyShowcaseSection) {
        familyShowcaseSection.addEventListener('mouseleave', function() {
            // تاخیر کوتاه برای اطمینان از اینکه کاربر واقعاً خارج شده
            setTimeout(() => {
                const isHoveringCard = document.querySelector('.family-collection-card:hover');
                // اگر روی هیچ کارتی هاور نیست، ویدیو را متوقف کن
                if (!isHoveringCard) {
                    stopFamilyVideo();
                }
            }, 100);
        });
    }

    // Preload تمام ویدیوها برای پخش سریعتر
    const familyVideos = document.querySelectorAll('.family-video');
    familyVideos.forEach(video => {
        video.addEventListener('loadeddata', function() {
            console.log('📹 Video loaded:', video.id);
        });
        video.addEventListener('error', function(e) {
            console.error('❌ Video loading error:', video.id, e);
        });
    });
    // === END FAMILY VIDEO INITIALIZATION (MERGED) ===
});