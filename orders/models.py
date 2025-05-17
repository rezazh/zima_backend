from django.db import models
from django.conf import settings
from products.models import Product
from users.models import Address


class Order(models.Model):
    """مدل سفارش"""
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('processing', 'در حال پردازش'),
        ('shipped', 'ارسال شده'),
        ('delivered', 'تحویل داده شده'),
        ('cancelled', 'لغو شده'),
        ('refunded', 'مسترد شده'),
    ]

    SHIPPING_CHOICES = [
        ('standard', 'ارسال عادی'),
        ('express', 'ارسال سریع'),
    ]

    PAYMENT_CHOICES = [
        ('online', 'پرداخت آنلاین'),
        ('cash', 'پرداخت در محل'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders',
                             verbose_name='کاربر')
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='orders', verbose_name='آدرس تحویل')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='وضعیت سفارش')
    shipping_method = models.CharField(max_length=20, choices=SHIPPING_CHOICES, default='standard',
                                       verbose_name='روش ارسال')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='online',
                                      verbose_name='روش پرداخت')

    subtotal = models.PositiveIntegerField(verbose_name='مجموع قیمت محصولات')
    discount = models.PositiveIntegerField(default=0, verbose_name='تخفیف')
    shipping_cost = models.PositiveIntegerField(default=0, verbose_name='هزینه ارسال')
    total_price = models.PositiveIntegerField(verbose_name='مبلغ کل')

    tracking_code = models.CharField(max_length=50, blank=True, null=True, verbose_name='کد پیگیری')
    transaction_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='شناسه تراکنش')

    description = models.TextField(blank=True, verbose_name='توضیحات سفارش')
    admin_note = models.TextField(blank=True, verbose_name='یادداشت مدیر')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ پرداخت')
    shipping_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ ارسال')
    delivery_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تحویل')

    class Meta:
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارش‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f"سفارش #{self.id} - {self.user.username}"

    def get_total_items(self):
        """تعداد کل آیتم‌های سفارش"""
        return sum(item.quantity for item in self.items.all())

    def is_paid(self):
        """آیا سفارش پرداخت شده است"""
        return self.status in ['paid', 'processing', 'shipped', 'delivered']

    def can_cancel(self):
        """آیا امکان لغو سفارش وجود دارد"""
        return self.status in ['pending', 'paid', 'processing']


class OrderItem(models.Model):
    """مدل آیتم‌های سفارش"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='سفارش')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items', verbose_name='محصول')

    quantity = models.PositiveIntegerField(default=1, verbose_name='تعداد')
    price = models.PositiveIntegerField(verbose_name='قیمت واحد')
    discount = models.PositiveIntegerField(default=0, verbose_name='درصد تخفیف')

    size = models.CharField(max_length=10, verbose_name='سایز')
    color = models.CharField(max_length=50, verbose_name='رنگ')

    class Meta:
        verbose_name = 'آیتم سفارش'
        verbose_name_plural = 'آیتم‌های سفارش'

    def __str__(self):
        return f"{self.quantity} عدد {self.product.name} - سفارش #{self.order.id}"

    def get_total_price(self):
        """محاسبه قیمت کل آیتم (بدون اعمال تخفیف)"""
        return self.price * self.quantity

    def get_discount_amount(self):
        """محاسبه مبلغ تخفیف"""
        if self.discount > 0:
            return (self.price * self.quantity * self.discount) / 100
        return 0

    def get_final_price(self):
        """محاسبه قیمت نهایی آیتم (با اعمال تخفیف)"""
        return self.get_total_price() - self.get_discount_amount()


class Payment(models.Model):
    """مدل پرداخت‌های سفارش"""
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('successful', 'موفق'),
        ('failed', 'ناموفق'),
        ('refunded', 'مسترد شده'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments', verbose_name='سفارش')
    amount = models.PositiveIntegerField(verbose_name='مبلغ پرداختی')
    transaction_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='شناسه تراکنش')
    reference_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='شناسه مرجع')

    gateway = models.CharField(max_length=50, verbose_name='درگاه پرداخت')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='وضعیت پرداخت')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'پرداخت'
        verbose_name_plural = 'پرداخت‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f"پرداخت {self.amount} تومان - سفارش #{self.order.id}"


class Shipment(models.Model):
    """مدل اطلاعات ارسال سفارش"""
    STATUS_CHOICES = [
        ('processing', 'در حال آماده‌سازی'),
        ('shipped', 'ارسال شده'),
        ('delivered', 'تحویل داده شده'),
        ('returned', 'مرجوع شده'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='shipments', verbose_name='سفارش')
    tracking_code = models.CharField(max_length=50, blank=True, null=True, verbose_name='کد پیگیری')
    carrier = models.CharField(max_length=100, verbose_name='شرکت حمل و نقل')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing', verbose_name='وضعیت ارسال')

    shipping_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ ارسال')
    estimated_delivery = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تخمینی تحویل')
    delivery_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تحویل')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'اطلاعات ارسال'
        verbose_name_plural = 'اطلاعات ارسال‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f"ارسال سفارش #{self.order.id} - {self.get_status_display()}"