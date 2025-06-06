# Generated by Django 5.1.5 on 2025-05-20 07:44

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0004_color_size_product_inventory_and_more'),
        ('users', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'در انتظار پرداخت'), ('paid', 'پرداخت شده'), ('processing', 'در حال پردازش'), ('shipped', 'ارسال شده'), ('delivered', 'تحویل داده شده'), ('cancelled', 'لغو شده'), ('refunded', 'مسترد شده')], default='pending', max_length=20, verbose_name='وضعیت سفارش')),
                ('shipping_method', models.CharField(choices=[('standard', 'ارسال عادی'), ('express', 'ارسال سریع')], default='standard', max_length=20, verbose_name='روش ارسال')),
                ('payment_method', models.CharField(choices=[('online', 'پرداخت آنلاین'), ('cash', 'پرداخت در محل')], default='online', max_length=20, verbose_name='روش پرداخت')),
                ('subtotal', models.PositiveIntegerField(verbose_name='مجموع قیمت محصولات')),
                ('discount', models.PositiveIntegerField(default=0, verbose_name='تخفیف')),
                ('shipping_cost', models.PositiveIntegerField(default=0, verbose_name='هزینه ارسال')),
                ('total_price', models.PositiveIntegerField(verbose_name='مبلغ کل')),
                ('tracking_code', models.CharField(blank=True, max_length=50, null=True, verbose_name='کد پیگیری')),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True, verbose_name='شناسه تراکنش')),
                ('description', models.TextField(blank=True, verbose_name='توضیحات سفارش')),
                ('admin_note', models.TextField(blank=True, verbose_name='یادداشت مدیر')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('payment_date', models.DateTimeField(blank=True, null=True, verbose_name='تاریخ پرداخت')),
                ('shipping_date', models.DateTimeField(blank=True, null=True, verbose_name='تاریخ ارسال')),
                ('delivery_date', models.DateTimeField(blank=True, null=True, verbose_name='تاریخ تحویل')),
                ('address', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='users.address', verbose_name='آدرس تحویل')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to=settings.AUTH_USER_MODEL, verbose_name='کاربر')),
            ],
            options={
                'verbose_name': 'سفارش',
                'verbose_name_plural': 'سفارش\u200cها',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='تعداد')),
                ('price', models.PositiveIntegerField(verbose_name='قیمت واحد')),
                ('discount', models.PositiveIntegerField(default=0, verbose_name='درصد تخفیف')),
                ('size', models.CharField(max_length=10, verbose_name='سایز')),
                ('color', models.CharField(max_length=50, verbose_name='رنگ')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='orders.order', verbose_name='سفارش')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='order_items', to='products.product', verbose_name='محصول')),
            ],
            options={
                'verbose_name': 'آیتم سفارش',
                'verbose_name_plural': 'آیتم\u200cهای سفارش',
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveIntegerField(verbose_name='مبلغ پرداختی')),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True, verbose_name='شناسه تراکنش')),
                ('reference_id', models.CharField(blank=True, max_length=100, null=True, verbose_name='شناسه مرجع')),
                ('gateway', models.CharField(max_length=50, verbose_name='درگاه پرداخت')),
                ('status', models.CharField(choices=[('pending', 'در انتظار پرداخت'), ('successful', 'موفق'), ('failed', 'ناموفق'), ('refunded', 'مسترد شده')], default='pending', max_length=20, verbose_name='وضعیت پرداخت')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='orders.order', verbose_name='سفارش')),
            ],
            options={
                'verbose_name': 'پرداخت',
                'verbose_name_plural': 'پرداخت\u200cها',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Shipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tracking_code', models.CharField(blank=True, max_length=50, null=True, verbose_name='کد پیگیری')),
                ('carrier', models.CharField(max_length=100, verbose_name='شرکت حمل و نقل')),
                ('status', models.CharField(choices=[('processing', 'در حال آماده\u200cسازی'), ('shipped', 'ارسال شده'), ('delivered', 'تحویل داده شده'), ('returned', 'مرجوع شده')], default='processing', max_length=20, verbose_name='وضعیت ارسال')),
                ('shipping_date', models.DateTimeField(blank=True, null=True, verbose_name='تاریخ ارسال')),
                ('estimated_delivery', models.DateTimeField(blank=True, null=True, verbose_name='تاریخ تخمینی تحویل')),
                ('delivery_date', models.DateTimeField(blank=True, null=True, verbose_name='تاریخ تحویل')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shipments', to='orders.order', verbose_name='سفارش')),
            ],
            options={
                'verbose_name': 'اطلاعات ارسال',
                'verbose_name_plural': 'اطلاعات ارسال\u200cها',
                'ordering': ['-created_at'],
            },
        ),
    ]
