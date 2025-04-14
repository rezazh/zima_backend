from django.contrib import admin
from .models import Product, ProductImage


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'is_featured')
    search_fields = ('name', 'brand')

@admin.register(ProductImage)
class ProductAdmin(admin.ModelAdmin):
    pass