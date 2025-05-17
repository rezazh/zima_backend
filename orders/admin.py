from django.contrib import admin
from .models import Order, OrderItem, Payment, Shipment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
    'product', 'quantity', 'price', 'discount', 'size', 'color', 'get_total_price', 'get_discount_amount',
    'get_final_price')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('created_at',)


class ShipmentInline(admin.TabularInline):
    model = Shipment
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'shipping_method', 'created_at')
    search_fields = ('id', 'user__username', 'user__email', 'tracking_code', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user', 'address')
    inlines = [OrderItemInline, PaymentInline, ShipmentInline]
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('user', 'address', 'status', 'tracking_code')
        }),
        ('اطلاعات مالی', {
            'fields': (
            'subtotal', 'discount', 'shipping_cost', 'total_price', 'payment_method', 'transaction_id', 'payment_date')
        }),
        ('اطلاعات ارسال', {
            'fields': ('shipping_method', 'shipping_date', 'delivery_date')
        }),
        ('توضیحات', {
            'fields': ('description', 'admin_note')
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:  # اگر در حال ویرایش یک سفارش موجود هستیم
            readonly_fields.extend(['user', 'subtotal', 'total_price'])
        return readonly_fields


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'status', 'gateway', 'transaction_id', 'created_at')
    list_filter = ('status', 'gateway', 'created_at')
    search_fields = ('order__id', 'transaction_id', 'reference_id')
    raw_id_fields = ('order',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'carrier', 'tracking_code', 'shipping_date', 'delivery_date')
    list_filter = ('status', 'carrier', 'shipping_date', 'delivery_date')
    search_fields = ('order__id', 'tracking_code')
    raw_id_fields = ('order',)
    readonly_fields = ('created_at', 'updated_at')