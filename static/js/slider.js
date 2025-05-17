document.addEventListener('DOMContentLoaded', function() {
    // انتخاب اسلایدر و اسلایدها
    const slider = document.getElementById('mainSlider');
    if (!slider) return; // اگر اسلایدر وجود نداشت، خارج شو

    const slides = slider.querySelectorAll('.slider-item');
    const dots = slider.querySelectorAll('.slider-dot');
    const prevButton = slider.querySelector('.slider-prev');
    const nextButton = slider.querySelector('.slider-next');

    // تعداد اسلایدها
    const slideCount = slides.length;
    let currentSlide = 0;
    let slideInterval;

    // تابع نمایش اسلاید با شماره مشخص
    function showSlide(index) {
        // اگر شماره اسلاید خارج از محدوده باشد
        if (index < 0) {
            index = slideCount - 1;
        } else if (index >= slideCount) {
            index = 0;
        }

        // حذف کلاس active از همه اسلایدها و دات‌ها
        slides.forEach(slide => slide.classList.remove('active'));
        dots.forEach(dot => dot.classList.remove('active'));

        // اضافه کردن کلاس active به اسلاید و دات فعلی
        slides[index].classList.add('active');
        dots[index].classList.add('active');

        // به‌روزرسانی شماره اسلاید فعلی
        currentSlide = index;
    }

    // تابع نمایش اسلاید بعدی
    function nextSlide() {
        showSlide(currentSlide + 1);
    }

    // تابع نمایش اسلاید قبلی
    function prevSlide() {
        showSlide(currentSlide - 1);
    }

    // شروع اسلاید خودکار
    function startSlideShow() {
        // اگر بیش از یک اسلاید داریم، اسلاید خودکار را شروع کن
        if (slideCount > 1) {
            slideInterval = setInterval(nextSlide, 5000); // هر 5 ثانیه
        }
    }

    // توقف اسلاید خودکار
    function stopSlideShow() {
        clearInterval(slideInterval);
    }

    // اضافه کردن رویداد کلیک به دکمه‌های قبلی و بعدی
    if (prevButton && nextButton) {
        prevButton.addEventListener('click', function() {
            prevSlide();
            stopSlideShow();
            startSlideShow();
        });

        nextButton.addEventListener('click', function() {
            nextSlide();
            stopSlideShow();
            startSlideShow();
        });
    }

    // اضافه کردن رویداد کلیک به دات‌ها
    dots.forEach(function(dot, index) {
        dot.addEventListener('click', function() {
            showSlide(index);
            stopSlideShow();
            startSlideShow();
        });
    });

    // اضافه کردن رویداد ماوس برای توقف اسلاید خودکار هنگام هاور
    slider.addEventListener('mouseenter', stopSlideShow);
    slider.addEventListener('mouseleave', startSlideShow);

    // شروع اسلاید خودکار
    startSlideShow();
});