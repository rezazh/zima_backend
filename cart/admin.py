from django.contrib import admin
from .models import CartItem, Coupon, WishlistItem

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'size', 'color', 'quantity', 'discount', 'get_total_price', 'get_final_price', 'created_at')
    list_filter = ('created_at', 'discount')
    search_fields = ('user__username', 'product__name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user', 'product')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'valid_from', 'valid_to', 'active', 'created_at')
    list_filter = ('active', 'valid_from', 'valid_to')
    search_fields = ('code', 'description')
    date_hierarchy = 'created_at'
    filter_horizontal = ('users',)

@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user', 'product')