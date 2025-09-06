from django.db import models
from django.db.models import Sum
from django.utils.text import slugify
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
import uuid
import os
from django.contrib.humanize.templatetags.humanize import intcomma # ✅ این خط را اضافه کنید


def get_product_image_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('products', str(instance.product.id), filename)


def get_category_image_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('categories', filename)


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='نام دسته‌بندی')
    slug = models.SlugField(max_length=120, unique=True, verbose_name='اسلاگ')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               related_name='children', verbose_name='دسته‌بندی والد')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    image = models.ImageField(
        upload_to=get_category_image_path,
        blank=True,
        verbose_name='تصویر',
        help_text=_('فرمت‌های مجاز: JPG, JPEG, PNG, GIF, WebP')
    )
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'
        ordering = ['name']

    def __str__(self):
        full_path = [self.name]
        parent = self.parent

        while parent is not None:
            full_path.append(parent.name)
            parent = parent.parent

        return ' > '.join(full_path[::-1])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('products:product_detail', kwargs={'slug': self.slug})

    def get_all_sizes(self):
        product_ids = self.products.filter(is_active=True).values_list('id', flat=True)
        return Size.objects.filter(
            productinventory__product_id__in=product_ids,
            productinventory__quantity__gt=0
        ).distinct().order_by('name')

    def get_all_colors(self):
        product_ids = self.products.filter(is_active=True).values_list('id', flat=True)
        return Color.objects.filter(
            productinventory__product_id__in=product_ids,
            productinventory__quantity__gt=0
        ).distinct().order_by('name')

    @property
    def get_products_count(self):
        return self.products.filter(is_active=True).count()



class Product(models.Model):
    """مدل محصولات"""
    GENDER_CHOICES = [
        ('men', 'مردانه'),
        ('women', 'زنانه'),
        ('unisex', 'یونیسکس'),
    ]

    name = models.CharField(max_length=200, verbose_name='نام محصول')
    slug = models.SlugField(max_length=220, unique=True, verbose_name='اسلاگ')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name='دسته‌بندی')
    brand = models.CharField(max_length=100, verbose_name='برند')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name='جنسیت')

    description = models.TextField(verbose_name='توضیحات')
    short_description = models.TextField(blank=True, verbose_name='توضیحات کوتاه')

    price = models.PositiveIntegerField(verbose_name='قیمت (تومان)')
    discount_percent = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100)],
                                                   verbose_name='درصد تخفیف')

    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_featured = models.BooleanField(default=False, verbose_name='محصول ویژه')

    sizes = models.JSONField(default=list, verbose_name='سایزها',
                             help_text='به صورت آرایه‌ای از سایزها مانند ["S", "M", "L"]')
    colors = models.JSONField(default=list, verbose_name='رنگ‌ها',
                              help_text='به صورت آرایه‌ای از رنگ‌ها مانند ["سفید", "مشکی", "آبی"]')
    color_codes = models.JSONField(default=list, verbose_name='کد رنگ‌ها',
                                   help_text='به صورت آرایه‌ای از کدهای رنگ مانند ["#FFFFFF", "#000000", "#0000FF"]')

    inventory = models.JSONField(default=dict, verbose_name='موجودی بر اساس رنگ و سایز',
                                 help_text='دیکشنری از موجودی هر ترکیب رنگ و سایز مانند {"S-سفید": 10, "M-سفید": 5}')

    price_adjustments = models.JSONField(default=dict, verbose_name='تغییرات قیمت',
                                         help_text='دیکشنری از تغییرات قیمت مانند {"S": 0, "M": 10000, "L": 20000}')

    weight = models.PositiveIntegerField(default=0, verbose_name='وزن (گرم)')
    dimensions = models.CharField(max_length=100, blank=True, verbose_name='ابعاد',
                                  help_text='مثال: 30x20x10 سانتی‌متر')

    meta_title = models.CharField(max_length=200, blank=True, verbose_name='عنوان متا')
    meta_description = models.TextField(blank=True, verbose_name='توضیحات متا')
    meta_keywords = models.CharField(max_length=300, blank=True, verbose_name='کلمات کلیدی متا')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    total_sales = models.PositiveIntegerField(default=0, verbose_name='تعداد فروش')

    class Meta:
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.meta_title:
            self.meta_title = self.name
        if not self.meta_description:
            self.meta_description = self.short_description or self.description[:160]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('products:detail', kwargs={'product_id': self.id})

    def get_display_price(self):
        """قیمت نمایشی محصول (با احتساب تخفیف)"""
        return self.get_discount_price()

    def get_available_sizes_display(self):
        """نمایش سایزهای موجود به صورت رشته"""
        sizes = self.get_available_sizes()
        return '-'.join([size.name for size in sizes]) if sizes else 'ناموجود'

    @property
    def is_new(self):
        """بررسی اینکه محصول جدید است یا نه (کمتر از 30 روز)"""
        from django.utils import timezone
        from datetime import timedelta
        return self.created_at >= timezone.now() - timedelta(days=30)


    def get_discount_price(self):
        if self.discount_percent > 0:
            discount_amount = (self.price * self.discount_percent) / 100
            return int(self.price - discount_amount)
        return self.price

    # ✅✅✅ متدهای جدید به اینجا (خارج از متد قبلی) منتقل شدند ✅✅✅
    def get_formatted_price(self):
        """قیمت اصلی محصول را با استفاده از فرمت‌بندی استاندارد پایتون کاماگذاری می‌کند."""
        try:
            price_int = int(self.price)
            # این روش به تنظیمات locale جنگو احترام می‌گذارد و جداکننده صحیح را استفاده می‌کند
            return f"{price_int:,}"
        except (ValueError, TypeError):
            return self.price

    def get_formatted_display_price(self):
        """قیمت نهایی (با تخفیف) را با استفاده از فرمت‌بندی استاندارد پایتون کاماگذاری می‌کند."""
        try:
            display_price_int = int(self.get_discount_price())
            # این روش به تنظیمات locale جنگو احترام می‌گذارد و جداکننده صحیح را استفاده می‌کند
            return f"{display_price_int:,}"
        except (ValueError, TypeError):
            return self.get_discount_price()


    def get_available_colors(self):
        from django.db.models import Q
        return Color.objects.filter(
            Q(productinventory__product=self) &
            Q(productinventory__quantity__gt=0)
        ).distinct()

    def get_available_sizes(self):
        from django.db.models import Q
        return Size.objects.filter(
            Q(productinventory__product=self) &
            Q(productinventory__quantity__gt=0)
        ).distinct()

    def get_inventory_for_color_size(self, color_id, size_id):
        try:
            return self.inventories.get(color_id=color_id, size_id=size_id)
        except ProductInventory.DoesNotExist:
            return None

    def get_price(self):
        return self.get_discount_price()

    def has_discount(self):
        return self.discount_percent > 0

    def in_stock(self):
        return self.is_in_stock

    def get_stock_for_variant(self, size, color):
        key = f"{size}-{color}"
        return self.inventory.get(key, 0)

    def get_price_for_size(self, size):
        base_price = self.get_discount_price()
        adjustment = self.price_adjustments.get(size, 0)
        return base_price + adjustment

    def get_color_info(self):
        result = []
        for i, color in enumerate(self.colors):
            code = self.color_codes[i] if i < len(self.color_codes) else "#000000"
            result.append({
                'name': color,
                'code': code
            })
        return result

    def get_main_image(self):
        main_image = self.images.filter(is_main=True).first()
        if main_image:
            return main_image
        return self.images.first()  # اگر تصویر اصلی نداشت، اولین تصویر را برگردان

    @property
    def total_stock(self):
        """موجودی کل محصول را از جمع موجودی‌های ProductInventory محاسبه می‌کند"""
        stock_sum = self.inventories.aggregate(total=Sum('quantity'))['total']
        return stock_sum or 0

    @property
    def is_in_stock(self):
        """بررسی می‌کند که آیا محصول بر اساس موجودی‌های رنگ و سایز، موجود است یا خیر"""
        return self.total_stock > 0

    def get_average_rating(self):
        from django.db.models import Avg
        avg_rating = self.reviews.aggregate(avg=Avg('rating'))['avg']
        return round(avg_rating, 1) if avg_rating else 0

    def get_rating_count(self):
        return self.reviews.count()


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name='محصول')
    image = models.ImageField(
        upload_to=get_product_image_path,
        verbose_name='تصویر',
        help_text=_('فرمت‌های مجاز: JPG, JPEG, PNG, GIF, WebP')
    )
    alt_text = models.CharField(max_length=200, blank=True, verbose_name='متن جایگزین')
    is_main = models.BooleanField(default=False, verbose_name='تصویر اصلی')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'تصویر محصول'
        verbose_name_plural = 'تصاویر محصول'
        ordering = ['-is_main', 'created_at']

    def __str__(self):
        return f"تصویر {self.product.name} - {self.id}"

    def save(self, *args, **kwargs):
        if not self.alt_text:
            self.alt_text = self.product.name

        if self.is_main:
            ProductImage.objects.filter(product=self.product, is_main=True).update(is_main=False)

        super().save(*args, **kwargs)


class ProductFeature(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='features', verbose_name='محصول')
    name = models.CharField(max_length=100, verbose_name='نام ویژگی')
    value = models.CharField(max_length=255, verbose_name='مقدار ویژگی')

    class Meta:
        verbose_name = 'ویژگی محصول'
        verbose_name_plural = 'ویژگی‌های محصول'
        unique_together = ['product', 'name']

    def __str__(self):
        return f"{self.name}: {self.value}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name='محصول')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews',
                             verbose_name='کاربر')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)],
                                              verbose_name='امتیاز')
    comment = models.TextField(verbose_name='نظر')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    is_approved = models.BooleanField(default=False, verbose_name='تایید شده')

    class Meta:
        verbose_name = 'نظر'
        verbose_name_plural = 'نظرات'
        ordering = ['-created_at']
        unique_together = ['product', 'user']  # هر کاربر فقط یک نظر می‌تواند برای هر محصول ثبت کند

    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating} ستاره"


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='نام تگ')
    slug = models.SlugField(max_length=120, unique=True, verbose_name='اسلاگ')
    products = models.ManyToManyField(Product, related_name='tags', blank=True, verbose_name='محصولات')

    class Meta:
        verbose_name = 'تگ'
        verbose_name_plural = 'تگ‌ها'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('products:tag', kwargs={'tag_slug': self.slug})


class Banner(models.Model):
    POSITION_CHOICES = [
        ('home_slider', 'اسلایدر صفحه اصلی'),
        ('home_top', 'بالای صفحه اصلی'),
        ('home_middle', 'وسط صفحه اصلی'),
        ('home_bottom', 'پایین صفحه اصلی'),
        ('category_top', 'بالای صفحه دسته‌بندی'),
        ('sidebar', 'ستون کناری'),
    ]

    title = models.CharField(max_length=200, verbose_name='عنوان')
    subtitle = models.CharField(max_length=300, blank=True, verbose_name='زیرعنوان')
    image = models.ImageField(
        upload_to='banners/',
        verbose_name='تصویر',
        help_text=_('فرمت‌های مجاز: JPG, JPEG, PNG, GIF, WebP')
    )
    url = models.URLField(verbose_name='لینک')
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, verbose_name='موقعیت')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='ترتیب نمایش')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    start_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ شروع نمایش')
    end_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ پایان نمایش')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'بنر تبلیغاتی'
        verbose_name_plural = 'بنرهای تبلیغاتی'
        ordering = ['position', 'order', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_position_display()}"

    def is_visible(self):
        from django.utils import timezone
        now = timezone.now()

        if not self.is_active:
            return False

        if self.start_date and self.start_date > now:
            return False

        if self.end_date and self.end_date < now:
            return False

        return True


class Color(models.Model):
    name = models.CharField(max_length=50, verbose_name='نام رنگ')

    @property
    def hex_code(self):
        """
        نام رنگ را به کد هگزادسیمال تبدیل می‌کند.
        این دیکشنری کامل شده بر اساس لیست ارسالی شماست.
        """
        color_map = {
            # خنثی
            'سفید': '#FFFFFF', 'مشکی': '#000000', 'خاکستری': '#808080', 'نقره‌ای': '#C0C0C0', 'کرم': '#FFFDD0',
            'بژ': '#F5F5DC', 'طوسی': '#808080', 'دودی': '#696969', 'زغالی': '#36454F', 'استخوانی': '#F9F6EE',
            'شیری': '#FDFFF5',

            # قرمز
            'قرمز': '#FF0000', 'زرشکی': '#8B0000', 'سرخابی': '#FC0FC0', 'لاکی': '#D21404', 'آجری': '#B22222',
            'سرخ': '#E30022', 'قرمز آتشین': '#FF4500', 'قرمز گیلاسی': '#D2042D', 'عنابی': '#722F37',
            'کالباسی': '#F08080', 'قرمز توت فرنگی': '#FC5A8D', 'جگری': '#800020', 'آلبالویی': '#8B0000',
            'قرمز گوجه‌ای': '#FF6347', 'شرابی': '#722F37',

            # صورتی
            'صورتی': '#FFC0CB', 'گلبهی': '#FFDAB9', 'صورتی کم‌رنگ': '#FFB6C1', 'صورتی تیره': '#FF69B4',
            'صورتی فوشیا': '#FF00FF', 'رز': '#FF007F', 'گلی': '#FFB5C5', 'صورتی پررنگ': '#DE3163',
            'صورتی چرک': '#D8A7B1', 'رزگلد': '#B76E79', 'صورتی پاستلی': '#F8C8DC', 'مرجانی': '#FF7F50',

            # نارنجی
            'نارنجی': '#FFA500', 'هلویی': '#FFE5B4', 'نارنجی تیره': '#FF8C00', 'نارنجی روشن': '#FFD580',
            'کهربایی': '#FFBF00', 'پرتقالی': '#FCA510', 'زردآلویی': '#FBCEB1', 'مسی': '#B87333',
            'نارنجی پرتقالی': '#FF7518', 'گل‌بهی': '#FFDAB9',

            # زرد
            'زرد': '#FFFF00', 'طلایی': '#FFD700', 'لیمویی': '#ADFF2F', 'زرد کم‌رنگ': '#FFFFE0',
            'زرد آفتابی': '#FFC72C', 'زرد کانولا': '#FFEF00', 'نباتی': '#F5DEB3', 'زرد لیمو': '#FFF44F',
            'زرد کره‌ای': '#FFFD74', 'برنزی': '#CD7F32', 'خردلی': '#FFDB58', 'زرد قناری': '#FFFF99',
            'کاهی': '#E8DEB5', 'نخودی': '#F2DDA4',

            # سبز
            'سبز': '#008000', 'سبز لجنی': '#556B2F', 'سبز یشمی': '#00A86B', 'سبز زیتونی': '#808000',
            'سبز تیره': '#006400', 'سبز روشن': '#90EE90', 'سبز جنگلی': '#228B22', 'سبز دریایی': '#2E8B57',
            'سبز چمنی': '#7CFC00', 'سبز فسفری': '#7FFF00', 'سبز نعنایی': '#98FF98', 'سبز کاج': '#01796F',
            'سبز پسته‌ای': '#93C572', 'سبز ارتشی': '#4B5320', 'سبزآبی': '#008080', 'سبز زمردی': '#50C878',
            'سبز سیدی': '#32CD32', 'سبز خزه‌ای': '#8A9A5B',

            # آبی
            'آبی': '#0000FF', 'آبی آسمانی': '#87CEEB', 'آبی نفتی': '#000080', 'فیروزه‌ای': '#40E0D0',
            'آبی روشن': '#ADD8E6', 'آبی تیره': '#00008B', 'آبی دریایی': '#000080', 'آبی یخی': '#99FFFF',
            'آبی الکتریک': '#7DF9FF', 'آبی کبالت': '#0047AB', 'سرمه‌ای': '#000080', 'لاجوردی': '#4169E1',
            'آبی پودری': '#B0E0E6', 'آبی کاربنی': '#0047AB', 'آبی درباری': '#4169E1', 'آبی پاستلی': '#A7C7E7',
            'کله غازی': '#008080', 'نیلی': '#5A4FCF',

            # بنفش
            'بنفش': '#8A2BE2', 'یاسی': '#C8A2C8', 'ارغوانی': '#9932CC', 'بنفش تیره': '#301934',
            'بنفش روشن': '#E6E6FA', 'بادمجانی': '#483D8B', 'ماژنتا': '#FF00FF', 'بنفش شاهی': '#800080',
            'بنفش پاستلی': '#B1A2C7', 'ویولت': '#8F00FF',

            # قهوه‌ای
            'قهوه‌ای': '#A52A2A', 'شکلاتی': '#D2691E', 'قهوه‌ای تیره': '#654321', 'قهوه‌ای روشن': '#C4A484',
            'خاکی': '#C2B280', 'کاراملی': '#C68E17', 'قهوه‌ای سوخته': '#3B2F2F', 'عسلی': '#D4AF37',
            'گندمی': '#F5DEB3', 'شنی': '#C2B280', 'زعفرانی': '#F4C430', 'حنایی': '#AB274F',
            'خرمایی': '#5C4033', 'نسکافه‌ای': '#826644', 'دارچینی': '#D2691E',

            # سایر
            'صدفی': '#FAF0E6', 'مروارید': '#E2DFD2', 'فیروزه': '#30D5C8',
            'پسته‌ای': '#93C572', 'بادامی': '#EED9C4', 'گردویی': '#725C42',
            'انار': '#C0362C', 'انگوری': '#6F2DA8', 'توتی': '#5A1F3C', 'نارگیلی': '#965A3E',
            'خاکستری موشی': '#9E9E9E', 'خاکستری نقره‌ای': '#C0C0C0',
        }
        return color_map.get(self.name, '#CCCCCC')  # رنگ پیش‌فرض برای موارد یافت نشده


    class Meta:
        verbose_name = 'رنگ'
        verbose_name_plural = 'رنگ‌ها'

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=20, verbose_name='نام سایز')

    class Meta:
        verbose_name = 'سایز'
        verbose_name_plural = 'سایزها'

    def __str__(self):
        return self.name


class ProductInventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventories', verbose_name='محصول')
    color = models.ForeignKey(Color, on_delete=models.CASCADE, verbose_name='رنگ')
    size = models.ForeignKey(Size, on_delete=models.CASCADE, verbose_name='سایز')
    quantity = models.PositiveIntegerField(default=0, verbose_name='موجودی')
    weight = models.PositiveIntegerField(default=0, help_text="وزن به گرم")
    dimensions = models.CharField(max_length=100, blank=True, help_text="ابعاد (مثال: 30x40x10)")

    class Meta:
        verbose_name = 'موجودی محصول'
        verbose_name_plural = 'موجودی محصولات'
        unique_together = ('product', 'color', 'size')

    def __str__(self):
        return f"{self.product.name} - {self.color.name} - {self.size.name} ({self.quantity})"

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'color_id': self.color_id,
            'color_name': self.color.name,
            'size_id': self.size_id,
            'size_name': self.size.name,
            'quantity': self.quantity
        }