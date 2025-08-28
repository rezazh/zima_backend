from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class CustomUser(AbstractUser):
    """مدل کاربر سفارشی با فیلدهای اضافی"""
    phone_number = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r'^09\d{9}$',
                message='شماره موبایل باید با 09 شروع شده و 11 رقم باشد.'
            )
        ],
        verbose_name='شماره موبایل',
        unique=True,
        null=True,
        blank=True
    )
    email = models.EmailField(_('email address'), unique=True)
    national_id = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^\d{10}$',
                message='کد ملی باید 10 رقم باشد.'
            )
        ],
        verbose_name='کد ملی',
        null=True,
        blank=True
    )
    birth_date = models.DateField(null=True, blank=True, verbose_name='تاریخ تولد')

    # تنظیمات اطلاع‌رسانی
    receive_sms = models.BooleanField(default=True, verbose_name='دریافت پیامک')
    receive_email = models.BooleanField(default=True, verbose_name='دریافت ایمیل')

    # تاریخ عضویت و آخرین بازدید
    date_modified = models.DateTimeField(auto_now=True, verbose_name='تاریخ آخرین بروزرسانی')
    last_visit = models.DateTimeField(null=True, blank=True, verbose_name='آخرین بازدید')

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'

    def __str__(self):
        return self.username

    def get_full_name(self):
        """نام و نام خانوادگی کاربر"""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.username

    def has_complete_profile(self):
        """بررسی تکمیل بودن پروفایل کاربر"""
        return bool(self.first_name and self.last_name and self.phone_number and self.email)


class Address(models.Model):
    """مدل آدرس کاربر"""
    PROVINCE_CHOICES = [
        ('تهران', 'تهران'),
        ('اصفهان', 'اصفهان'),
        ('فارس', 'فارس'),
        ('خراسان رضوی', 'خراسان رضوی'),
        ('آذربایجان شرقی', 'آذربایجان شرقی'),
        ('آذربایجان غربی', 'آذربایجان غربی'),
        ('کرمان', 'کرمان'),
        ('خوزستان', 'خوزستان'),
        ('هرمزگان', 'هرمزگان'),
        ('سیستان و بلوچستان', 'سیستان و بلوچستان'),
        ('کردستان', 'کردستان'),
        ('همدان', 'همدان'),
        ('کرمانشاه', 'کرمانشاه'),
        ('گیلان', 'گیلان'),
        ('مازندران', 'مازندران'),
        ('زنجان', 'زنجان'),
        ('گلستان', 'گلستان'),
        ('اردبیل', 'اردبیل'),
        ('قزوین', 'قزوین'),
        ('لرستان', 'لرستان'),
        ('بوشهر', 'بوشهر'),
        ('کهگیلویه و بویراحمد', 'کهگیلویه و بویراحمد'),
        ('مرکزی', 'مرکزی'),
        ('ایلام', 'ایلام'),
        ('چهارمحال و بختیاری', 'چهارمحال و بختیاری'),
        ('یزد', 'یزد'),
        ('قم', 'قم'),
        ('سمنان', 'سمنان'),
        ('البرز', 'البرز'),
        ('خراسان شمالی', 'خراسان شمالی'),
        ('خراسان جنوبی', 'خراسان جنوبی'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses', verbose_name='کاربر')
    title = models.CharField(max_length=100, verbose_name='عنوان آدرس', help_text='مثال: خانه، محل کار و...')
    receiver_full_name = models.CharField(max_length=150, verbose_name='نام و نام خانوادگی گیرنده')
    receiver_phone = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r'^09\d{9}$',
                message='شماره موبایل باید با 09 شروع شده و 11 رقم باشد.'
            )
        ],
        verbose_name='شماره موبایل گیرنده'
    )
    province = models.CharField(max_length=50, choices=PROVINCE_CHOICES, verbose_name='استان')
    city = models.CharField(max_length=50, verbose_name='شهر')
    postal_code = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^\d{10}$',
                message='کد پستی باید 10 رقم باشد.'
            )
        ],
        verbose_name='کد پستی'
    )
    full_address = models.TextField(verbose_name='آدرس کامل')
    is_default = models.BooleanField(default=False, verbose_name='آدرس پیش‌فرض')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'آدرس'
        verbose_name_plural = 'آدرس‌ها'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.province}, {self.city}"

    def save(self, *args, **kwargs):
        """اگر این آدرس به عنوان پیش‌فرض انتخاب شده، سایر آدرس‌های کاربر از حالت پیش‌فرض خارج شوند"""
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class UserActivity(models.Model):
    """مدل فعالیت‌های کاربر"""
    ACTIVITY_TYPES = [
        ('login', 'ورود به سیستم'),
        ('logout', 'خروج از سیستم'),
        ('register', 'ثبت‌نام'),
        ('profile_update', 'بروزرسانی پروفایل'),
        ('password_change', 'تغییر رمز عبور'),
        ('order_placed', 'ثبت سفارش'),
        ('review_added', 'ثبت نظر'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activities', verbose_name='کاربر')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, verbose_name='نوع فعالیت')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='آدرس IP')
    user_agent = models.TextField(null=True, blank=True, verbose_name='مرورگر کاربر')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='زمان فعالیت')
    details = models.JSONField(null=True, blank=True, verbose_name='جزئیات')

    class Meta:
        verbose_name = 'فعالیت کاربر'
        verbose_name_plural = 'فعالیت‌های کاربران'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.timestamp}"


class Newsletter(models.Model):
    """مدل خبرنامه"""
    email = models.EmailField(unique=True, verbose_name='ایمیل')
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='newsletters',
                             verbose_name='کاربر')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ عضویت')

    class Meta:
        verbose_name = 'خبرنامه'
        verbose_name_plural = 'خبرنامه‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return self.email


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = 'علاقه‌مندی'
        verbose_name_plural = 'علاقه‌مندی‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.product.name}'