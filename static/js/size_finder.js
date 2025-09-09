// Size Finder - ابزار پیدا کننده سایز زیما
class SizeFinder {
  constructor() {
    this.currentStep = 1;
    this.selectedProduct = null;
    this.measurements = {};
    this.result = null;

    this.init();
  }

  init() {
    this.createModal();
    this.bindEvents();
  }

  createModal() {
    const modalHTML = `
      <div class="size-finder-overlay" id="sizeFinderModal">
        <div class="size-finder-modal">
          <div class="finder-header">
            <button class="finder-close" id="closeSizeFinder" aria-label="بستن">
              <i class="fas fa-times"></i>
            </button>
            <h2 class="finder-title">پیدا کننده سایز هوشمند</h2>
            <p class="finder-subtitle">سایز مناسب خود را در چند قدم ساده پیدا کنید</p>
            <div class="finder-progress">
              <div class="finder-progress-bar" id="finderProgressBar" style="width: 25%"></div>
            </div>
          </div>

          <div class="finder-content">
            <!-- مرحله 1: انتخاب محصول -->
            <div class="finder-step active" id="step1">
              <div class="step-header">
                <div class="step-number">1</div>
                <h3 class="step-title">نوع محصول را انتخاب کنید</h3>
                <p class="step-description">کدام محصول را می‌خواهید سایز آن را پیدا کنید؟</p>
              </div>

              <div class="product-grid">
                <div class="product-option" data-product="bra">
                  <div class="product-icon">👙</div>
                  <h4 class="product-name">سوتین</h4>
                </div>
                <div class="product-option" data-product="panties">
                  <div class="product-icon">🩲</div>
                  <h4 class="product-name">شورت</h4>
                </div>
                <div class="product-option" data-product="nightwear">
                  <div class="product-icon">🌙</div>
                  <h4 class="product-name">لباس خواب</h4>
                </div>
                <div class="product-option" data-product="sportswear">
                  <div class="product-icon">🏃‍♀️</div>
                  <h4 class="product-name">لباس ورزشی</h4>
                </div>
              </div>

              <div class="finder-actions">
                <button class="finder-btn primary" id="nextStep1" disabled>
                  <i class="fas fa-arrow-left"></i>
                  مرحله بعد
                </button>
              </div>
            </div>

            <!-- مرحله 2: اندازه‌گیری -->
            <div class="finder-step" id="step2">
              <div class="step-header">
                <div class="step-number">2</div>
                <h3 class="step-title">اندازه‌های بدن خود را وارد کنید</h3>
                <p class="step-description">برای دقت بیشتر، از متر خیاطی استفاده کنید</p>
              </div>

              <div class="measurements-form" id="measurementsForm">
                <!-- فرم اندازه‌گیری بر اساس محصول انتخاب شده -->
              </div>

              <div class="error-message" id="measurementError">
                لطفاً همه فیلدها را با اعداد معتبر پر کنید
              </div>

              <div class="finder-actions">
                <button class="finder-btn secondary" id="prevStep2">
                  <i class="fas fa-arrow-right"></i>
                  مرحله قبل
                </button>
                <button class="finder-btn primary" id="calculateSize">
                  <i class="fas fa-calculator"></i>
                  محاسبه سایز
                </button>
              </div>
            </div>

            <!-- مرحله 3: نتیجه -->
            <div class="finder-step" id="step3">
              <div class="step-header">
                <div class="step-number">3</div>
                <h3 class="step-title">سایز مناسب شما</h3>
                <p class="step-description">بر اساس اندازه‌هایی که وارد کردید</p>
              </div>

              <div class="result-container" id="resultContainer">
                <!-- نتیجه محاسبه -->
              </div>

              <div class="finder-actions">
                <button class="finder-btn secondary" id="startOver">
                  <i class="fas fa-redo"></i>
                  شروع مجدد
                </button>
                <button class="finder-btn primary" id="viewProducts">
                  <i class="fas fa-shopping-bag"></i>
                  مشاهده محصولات
                </button>
              </div>
            </div>

            <!-- حالت لودینگ -->
            <div class="finder-loading" id="finderLoading">
              <div class="loading-spinner"></div>
              <p class="loading-text">در حال محاسبه سایز مناسب شما...</p>
            </div>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
  }

  bindEvents() {
    // باز کردن modal
    const heroButton = document.querySelector('.hero-cta');
    if (heroButton) {
      heroButton.addEventListener('click', (e) => {
        e.preventDefault();
        this.openModal();
      });
    }

    // بستن modal
    document.getElementById('closeSizeFinder').addEventListener('click', () => {
      this.closeModal();
    });

    // بستن با کلیک روی overlay
    document.getElementById('sizeFinderModal').addEventListener('click', (e) => {
      if (e.target.classList.contains('size-finder-overlay')) {
        this.closeModal();
      }
    });

    // بستن با کلید Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isModalOpen()) {
        this.closeModal();
      }
    });

    // انتخاب محصول
    document.addEventListener('click', (e) => {
      if (e.target.closest('.product-option')) {
        this.selectProduct(e.target.closest('.product-option'));
      }
    });

    // دکمه‌های ناوبری
    document.getElementById('nextStep1').addEventListener('click', () => {
      this.goToStep(2);
    });

    document.getElementById('prevStep2').addEventListener('click', () => {
      this.goToStep(1);
    });

    document.getElementById('calculateSize').addEventListener('click', () => {
      this.calculateSize();
    });

    document.getElementById('startOver').addEventListener('click', () => {
      this.resetFinder();
    });

    document.getElementById('viewProducts').addEventListener('click', () => {
      this.viewProducts();
    });
  }

  openModal() {
    document.getElementById('sizeFinderModal').classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  closeModal() {
    document.getElementById('sizeFinderModal').classList.remove('active');
    document.body.style.overflow = '';
  }

  isModalOpen() {
    return document.getElementById('sizeFinderModal').classList.contains('active');
  }

  selectProduct(element) {
    // حذف انتخاب قبلی
    document.querySelectorAll('.product-option').forEach(option => {
      option.classList.remove('selected');
    });

    // انتخاب جدید
    element.classList.add('selected');
    this.selectedProduct = element.dataset.product;

    // فعال کردن دکمه مرحله بعد
    document.getElementById('nextStep1').disabled = false;

    // ایجاد فرم اندازه‌گیری
    this.createMeasurementForm();
  }

  createMeasurementForm() {
    const formContainer = document.getElementById('measurementsForm');
    let formHTML = '';

    const measurementConfigs = {
      bra: [
        { key: 'underbust', label: 'دور زیر سینه', icon: 'fas fa-ruler-horizontal', tip: 'متر را محکم اما راحت زیر سینه‌ها بپیچید' },
        { key: 'bust', label: 'دور سینه', icon: 'fas fa-ruler-horizontal', tip: 'از روی برجسته‌ترین قسمت سینه اندازه‌گیری کنید' }
      ],
      panties: [
        { key: 'waist', label: 'دور کمر', icon: 'fas fa-ruler-horizontal', tip: 'باریک‌ترین قسمت کمر را اندازه‌گیری کنید' },
        { key: 'hips', label: 'دور باسن', icon: 'fas fa-ruler-horizontal', tip: 'از روی برجسته‌ترین قسمت باسن اندازه‌گیری کنید' }
      ],
      nightwear: [
        { key: 'bust', label: 'دور سینه', icon: 'fas fa-ruler-horizontal', tip: 'از روی برجسته‌ترین قسمت سینه' },
        { key: 'waist', label: 'دور کمر', icon: 'fas fa-ruler-horizontal', tip: 'باریک‌ترین قسمت کمر' },
        { key: 'hips', label: 'دور باسن', icon: 'fas fa-ruler-horizontal', tip: 'برجسته‌ترین قسمت باسن' }
      ],
      sportswear: [
        { key: 'bust', label: 'دور سینه', icon: 'fas fa-ruler-horizontal', tip: 'برای سوتین ورزشی' },
        { key: 'underbust', label: 'دور زیر سینه', icon: 'fas fa-ruler-horizontal', tip: 'برای سوتین ورزشی' },
        { key: 'waist', label: 'دور کمر', icon: 'fas fa-ruler-horizontal', tip: 'برای لگ و تاپ' },
        { key: 'hips', label: 'دور باسن', icon: 'fas fa-ruler-horizontal', tip: 'برای لگ ورزشی' }
      ]
    };

    const measurements = measurementConfigs[this.selectedProduct] || [];

    measurements.forEach(measurement => {
      formHTML += `
        <div class="measurement-group">
          <label class="measurement-label">
            <i class="${measurement.icon} measurement-icon"></i>
            ${measurement.label}
          </label>
          <div class="measurement-input-group">
            <input 
              type="number" 
              class="measurement-input" 
              id="${measurement.key}" 
              placeholder="مثال: 75"
              min="50" 
              max="150"
              step="0.5"
            >
            <div class="measurement-unit">سانتی‌متر</div>
          </div>
          <div class="measurement-tip">
            <i class="fas fa-info-circle"></i>
            ${measurement.tip}
          </div>
        </div>
      `;
    });

    formContainer.innerHTML = formHTML;

    // اضافه کردن event listener برای validation
    formContainer.querySelectorAll('.measurement-input').forEach(input => {
      input.addEventListener('input', () => {
        this.validateInput(input);
      });
    });
  }

  validateInput(input) {
    const value = parseFloat(input.value);
    const min = parseFloat(input.min);
    const max = parseFloat(input.max);

    if (isNaN(value) || value < min || value > max) {
      input.classList.add('error');
      return false;
    } else {
      input.classList.remove('error');
      return true;
    }
  }

  goToStep(stepNumber) {
    // مخفی کردن همه مراحل
    document.querySelectorAll('.finder-step').forEach(step => {
      step.classList.remove('active');
    });

    // نمایش مرحله مورد نظر
    document.getElementById(`step${stepNumber}`).classList.add('active');
    this.currentStep = stepNumber;

    // بروزرسانی progress bar
    const progress = (stepNumber / 3) * 100;
    document.getElementById('finderProgressBar').style.width = `${progress}%`;
  }

  calculateSize() {
    // جمع‌آوری اندازه‌ها
    const inputs = document.querySelectorAll('.measurement-input');
    let isValid = true;
    this.measurements = {};

    inputs.forEach(input => {
      const value = parseFloat(input.value);
      if (!this.validateInput(input)) {
        isValid = false;
      } else {
        this.measurements[input.id] = value;
      }
    });

    if (!isValid) {
      document.getElementById('measurementError').classList.add('show');
      return;
    }

    document.getElementById('measurementError').classList.remove('show');

    // نمایش لودینگ
    document.querySelectorAll('.finder-step').forEach(step => {
      step.classList.remove('active');
    });
    document.getElementById('finderLoading').classList.add('show');

    // شبیه‌سازی محاسبه (در پروژه واقعی ممکن است API call باشد)
    setTimeout(() => {
      this.result = this.performSizeCalculation();
      this.showResult();
      document.getElementById('finderLoading').classList.remove('show');
      this.goToStep(3);
    }, 2000);
  }

  performSizeCalculation() {
    const { selectedProduct, measurements } = this;
    let result = {};

    switch (selectedProduct) {
      case 'bra':
        result = this.calculateBraSize(measurements);
        break;
      case 'panties':
        result = this.calculatePantiesSize(measurements);
        break;
      case 'nightwear':
        result = this.calculateNightwearSize(measurements);
        break;
      case 'sportswear':
        result = this.calculateSportswearSize(measurements);
        break;
    }

    return result;
  }

  calculateBraSize(measurements) {
    const { underbust, bust } = measurements;

    // محاسبه سایز بند
    let bandSize;
    if (underbust >= 63 && underbust <= 67) bandSize = '65';
    else if (underbust >= 68 && underbust <= 72) bandSize = '70';
    else if (underbust >= 73 && underbust <= 77) bandSize = '75';
    else if (underbust >= 78 && underbust <= 82) bandSize = '80';
    else if (underbust >= 83 && underbust <= 87) bandSize = '85';
    else bandSize = '90';

    // محاسبه کاپ
    const difference = bust - underbust;
    let cupSize;
    if (difference >= 12 && difference <= 13) cupSize = 'A';
    else if (difference >= 14 && difference <= 15) cupSize = 'B';
    else if (difference >= 16 && difference <= 17) cupSize = 'C';
    else if (difference >= 18 && difference <= 19) cupSize = 'D';
    else cupSize = 'DD';

    return {
      size: `${bandSize}${cupSize}`,
      bandSize,
      cupSize,
      confidence: 'بالا',
      description: `سایز ${bandSize}${cupSize} برای شما مناسب است`,
      details: {
        'سایز بند': bandSize,
        'سایز کاپ': cupSize,
        'تفاوت اندازه': `${difference.toFixed(1)} سانتی‌متر`,
        'دور زیر سینه شما': `${underbust} سانتی‌متر`,
        'دور سینه شما': `${bust} سانتی‌متر`
      },
      tips: [
        'سوتین باید محکم اما راحت باشد',
        'کاپ باید کاملاً سینه را بپوشاند',
        'بندها نباید در شانه فرو روند'
      ]
    };
  }

  calculatePantiesSize(measurements) {
    const { waist, hips } = measurements;

    let size;
    if (waist <= 62 && hips <= 86) size = 'XS';
    else if (waist <= 67 && hips <= 91) size = 'S';
    else if (waist <= 72 && hips <= 96) size = 'M';
    else if (waist <= 77 && hips <= 101) size = 'L';
    else size = 'XL';

    return {
      size,
      confidence: 'بالا',
      description: `سایز ${size} برای شما مناسب است`,
      details: {
        'سایز توصیه شده': size,
        'دور کمر شما': `${waist} سانتی‌متر`,
        'دور باسن شما': `${hips} سانتی‌متر`
      },
      tips: [
        'شورت نباید خیلی تنگ یا گشاد باشد',
        'پارچه باید روی پوست نرم و راحت باشد',
        'طرح‌های دانتل ممکن است کمی تنگ‌تر باشند'
      ]
    };
  }

  calculateNightwearSize(measurements) {
    const { bust, waist, hips } = measurements;

    let size;
    if (bust <= 86 && waist <= 67 && hips <= 91) size = 'S';
    else if (bust <= 91 && waist <= 72 && hips <= 96) size = 'M';
    else if (bust <= 96 && waist <= 77 && hips <= 101) size = 'L';
    else size = 'XL';

    return {
      size,
      confidence: 'بالا',
      description: `سایز ${size} برای لباس خواب مناسب است`,
      details: {
        'سایز توصیه شده': size,
        'دور سینه شما': `${bust} سانتی‌متر`,
        'دور کمر شما': `${waist} سانتی‌متر`,
        'دور باسن شما': `${hips} سانتی‌متر`
      },
      tips: [
        'لباس خواب باید کاملاً راحت باشد',
        'برای خوابیدن کمی گشادتر بهتر است',
        'پارچه باید تنفس‌پذیر باشد'
      ]
    };
  }

  calculateSportswearSize(measurements) {
    const { bust, underbust, waist, hips } = measurements;

    // سایز سوتین ورزشی
    let braSize;
    if (underbust <= 67 && bust <= 82) braSize = 'XS';
    else if (underbust <= 72 && bust <= 87) braSize = 'S';
    else if (underbust <= 77 && bust <= 92) braSize = 'M';
    else if (underbust <= 82 && bust <= 97) braSize = 'L';
    else braSize = 'XL';

    // سایز لگ
    let leggingsSize;
    if (waist <= 64 && hips <= 89) leggingsSize = 'XS';
    else if (waist <= 69 && hips <= 94) leggingsSize = 'S';
    else if (waist <= 74 && hips <= 99) leggingsSize = 'M';
    else if (waist <= 79 && hips <= 104) leggingsSize = 'L';
    else leggingsSize = 'XL';

    return {
      size: braSize === leggingsSize ? braSize : `${braSize}/${leggingsSize}`,
      confidence: 'بالا',
      description: braSize === leggingsSize ?
        `سایز ${braSize} برای ست ورزشی مناسب است` :
        `سوتین ${braSize} و لگ ${leggingsSize} برای شما مناسب است`,
      details: {
        'سوتین ورزشی': braSize,
        'لگ و تاپ': leggingsSize,
        'دور سینه شما': `${bust} سانتی‌متر`,
        'دور زیر سینه شما': `${underbust} سانتی‌متر`,
        'دور کمر شما': `${waist} سانتی‌متر`,
        'دور باسن شما': `${hips} سانتی‌متر`
      },
      tips: [
        'لباس ورزشی باید کشسان و انعطاف‌پذیر باشد',
        'سوتین ورزشی باید ساپورت کافی داشته باشد',
        'پارچه باید عرق را جذب کند'
      ]
    };
  }

  showResult() {
    const resultContainer = document.getElementById('resultContainer');
    const { result } = this;

    let resultHTML = `
      <div class="result-icon">
        <i class="fas fa-check-circle"></i>
      </div>
      <h3 class="result-title">سایز مناسب شما</h3>
      <div class="result-size">${result.size}</div>
      <p class="result-description">${result.description}</p>
      
      <div class="result-details">
        <h4>جزئیات اندازه‌گیری:</h4>
        <ul>
    `;

    for (const [label, value] of Object.entries(result.details)) {
      resultHTML += `
        <li>
          <span class="label">${label}:</span>
          <span class="value">${value}</span>
        </li>
      `;
    }

    resultHTML += `
        </ul>
      </div>

      <div class="result-details">
        <h4>نکات مفید:</h4>
        <ul>
    `;

    result.tips.forEach(tip => {
      resultHTML += `
        <li>
          <span class="label">•</span>
          <span class="value">${tip}</span>
        </li>
      `;
    });

    resultHTML += `
        </ul>
      </div>
    `;

    resultContainer.innerHTML = resultHTML;
  }

  resetFinder() {
    this.currentStep = 1;
    this.selectedProduct = null;
    this.measurements = {};
    this.result = null;

    // بازگشت به مرحله اول
    this.goToStep(1);

    // پاک کردن انتخاب‌ها
    document.querySelectorAll('.product-option').forEach(option => {
      option.classList.remove('selected');
    });

    document.getElementById('nextStep1').disabled = true;
    document.getElementById('measurementError').classList.remove('show');
  }

  viewProducts() {
    // هدایت به صفحه محصولات با فیلتر سایز
    const productUrls = {
      bra: '/products/?category=bra',
      panties: '/products/?category=panties',
      nightwear: '/products/?category=nightwear',
      sportswear: '/products/?category=sportswear'
    };

    const targetUrl = productUrls[this.selectedProduct] || '/products/';

    // اضافه کردن سایز به URL
    const sizeParam = `&size=${encodeURIComponent(this.result.size)}`;

    this.closeModal();
    window.location.href = targetUrl + sizeParam;
  }
}

// راه‌اندازی Size Finder
document.addEventListener('DOMContentLoaded', function() {
  window.sizeFinder = new SizeFinder();
});