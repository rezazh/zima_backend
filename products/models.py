from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
import uuid
import os


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
        return reverse('products:category', kwargs={'category_slug': self.slug})

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

    stock = models.PositiveIntegerField(default=0, verbose_name='موجودی')
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

    def get_discount_price(self):
        if self.discount_percent > 0:
            discount_amount = (self.price * self.discount_percent) / 100
            return int(self.price - discount_amount)
        return self.price

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
        return self.stock > 0

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