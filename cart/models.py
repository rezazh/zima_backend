from django.db import models
from django.conf import settings
from django.utils import timezone
from products.models import Product, ProductInventory


class CartItem(models.Model):
    """مدل آیتم سبد خرید"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=10)
    color = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=1)
    discount = models.PositiveIntegerField(default=0)  # درصد تخفیف
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    inventory = models.ForeignKey(ProductInventory, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'آیتم سبد خرید'
        verbose_name_plural = 'آیتم‌های سبد خرید'
        unique_together = ['user', 'product', 'size', 'color']  # هر محصول با سایز و رنگ مشخص فقط یکبار در سبد باشد

    def __str__(self):
        return f"{self.quantity} عدد {self.product.name} ({self.size}, {self.color}) - کاربر: {self.user.username}"

    def get_total_price(self):
        """محاسبه قیمت کل آیتم (بدون اعمال تخفیف)"""
        return self.product.price * self.quantity

    def get_discount_amount(self):
        """محاسبه مبلغ تخفیف"""
        if self.discount > 0:
            return (self.product.price * self.quantity * self.discount) / 100
        return 0

    def get_final_price(self):
        """محاسبه قیمت نهایی آیتم (با اعمال تخفیف)"""
        return self.get_total_price() - self.get_discount_amount()


class Coupon(models.Model):
    """مدل کد تخفیف"""
    code = models.CharField(max_length=50, unique=True, verbose_name='کد تخفیف')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    discount_percent = models.PositiveIntegerField(verbose_name='درصد تخفیف')
    valid_from = models.DateTimeField(verbose_name='تاریخ شروع اعتبار')
    valid_to = models.DateTimeField(verbose_name='تاریخ پایان اعتبار')
    min_purchase = models.PositiveIntegerField(default=0, verbose_name='حداقل مبلغ خرید')
    max_discount = models.PositiveIntegerField(default=0, verbose_name='حداکثر مبلغ تخفیف')
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='coupons',
                                   verbose_name='کاربران استفاده کننده')
    active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'کد تخفیف'
        verbose_name_plural = 'کدهای تخفیف'

    def __str__(self):
        return f"{self.code} - {self.discount_percent}%"

    def is_valid(self):
        """بررسی معتبر بودن کد تخفیف"""
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to

    def is_valid_for_user(self, user):
        """بررسی اینکه آیا کاربر می‌تواند از این کد تخفیف استفاده کند"""
        # اگر کاربر قبلاً از این کد استفاده کرده باشد
        if self.users.filter(id=user.id).exists():
            return False
        return True

    def calculate_discount(self, total_amount):
        """محاسبه مبلغ تخفیف بر اساس مبلغ کل خرید"""
        if total_amount < self.min_purchase:
            return 0

        discount_amount = (total_amount * self.discount_percent) / 100

        # اعمال محدودیت حداکثر مبلغ تخفیف
        if self.max_discount > 0 and discount_amount > self.max_discount:
            discount_amount = self.max_discount

        return discount_amount


class WishlistItem(models.Model):
    """مدل آیتم لیست علاقه‌مندی‌ها"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'آیتم لیست علاقه‌مندی‌ها'
        verbose_name_plural = 'آیتم‌های لیست علاقه‌مندی‌ها'
        unique_together = ['user', 'product']  # هر محصول فقط یکبار در لیست علاقه‌مندی‌های کاربر باشد

    def __str__(self):
        return f"{self.product.name} - کاربر: {self.user.username}"