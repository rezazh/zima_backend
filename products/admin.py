from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, Tag, Review, ProductInventory, Color, Size, ProductFeature, Banner


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_main', 'display_image')
    readonly_fields = ('display_image',)

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" />', obj.image.url)
        return "بدون تصویر"

    display_image.short_description = "پیش‌نمایش"


class ProductInventoryInline(admin.TabularInline):
    model = ProductInventory
    extra = 1
    fields = ('color', 'size', 'quantity')


class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 1
    fields = ('name', 'value')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
    'display_image', 'name', 'category', 'price', 'get_discount_price', 'is_active', 'is_featured', 'created_at')
    list_filter = ('is_active', 'is_featured', 'category', 'brand', 'gender', 'created_at')
    search_fields = ('name', 'description', 'brand')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'is_featured')
    inlines = [ProductImageInline, ProductFeatureInline, ProductInventoryInline]

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'slug', 'category', 'brand', 'gender', 'is_active', 'is_featured')
        }),
        ('توضیحات', {
            'fields': ('description', 'short_description')
        }),
        ('قیمت‌گذاری', {
            'fields': ('price', 'discount_percent')
        }),
        ('موجودی و ویژگی‌ها', {
            'fields': ('stock', 'weight')
        }),
        ('مشخصات فیزیکی', {
            'fields': ('dimensions',),
            'description': 'ابعاد محصول را وارد کنید. مثال: عرض شانه: 45 سانتی‌متر، قد: 70 سانتی‌متر'
        }),
        ('سئو', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
    )

    def get_discount_price(self, obj):
        return obj.get_discount_price()

    get_discount_price.short_description = "قیمت با تخفیف"

    def display_image(self, obj):
        """نمایش تصویر اصلی محصول در لیست محصولات"""
        main_image = obj.get_main_image()
        if main_image and main_image.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                               main_image.image.url)
        return "بدون تصویر"

    display_image.short_description = "تصویر"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('display_image', 'name', 'parent', 'is_active', 'get_products_count')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

    def get_products_count(self, obj):
        return obj.get_products_count

    get_products_count.short_description = "تعداد محصولات"

    def display_image(self, obj):
        """نمایش تصویر دسته‌بندی در لیست دسته‌بندی‌ها"""
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "بدون تصویر"

    display_image.short_description = "تصویر"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'display_image', 'is_main', 'alt_text')
    list_filter = ('is_main', 'product')
    search_fields = ('product__name', 'alt_text')

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" />', obj.image.url)
        return "بدون تصویر"

    display_image.short_description = "پیش‌نمایش"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')
    list_editable = ('is_approved',)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name',)  # حذف 'order' از list_display
    search_fields = ('name',)
    # حذف list_editable


@admin.register(ProductInventory)
class ProductInventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'color', 'size', 'quantity', 'weight', 'dimensions')
    list_filter = ('product', 'color', 'size')
    search_fields = ('product__name', 'color__name', 'size__name')

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('product', 'color', 'size', 'quantity')
        }),
        ('مشخصات فیزیکی', {
            'fields': ('weight', 'dimensions'),
            'classes': ('collapse',),
            'description': 'مشخصات فیزیکی مختص این سایز و رنگ را وارد کنید.'
        }),
    )

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('products',)


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('display_image', 'title', 'position', 'order', 'is_active')
    list_filter = ('position', 'is_active')
    search_fields = ('title', 'subtitle')
    list_editable = ('is_active', 'order')

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "بدون تصویر"

    display_image.short_description = "تصویر"


@admin.register(ProductFeature)
class ProductFeatureAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'value')
    list_filter = ('product',)
    search_fields = ('product__name', 'name', 'value')