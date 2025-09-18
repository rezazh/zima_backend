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
        'display_image', 'name', 'price', 'get_discount_price',
        'total_stock', 'is_active', 'is_featured', 'created_at'
    )
    list_filter = ('is_active', 'is_featured', 'categories', 'brand', 'gender', 'created_at')
    search_fields = ('name', 'description', 'brand')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('categories',) # نمایش دسته‌بندی‌ها به صورت رابط کاربری بهتر (Multiple Select)
    list_editable = ('is_active', 'is_featured')
    inlines = [ProductImageInline, ProductFeatureInline, ProductInventoryInline]

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'slug', 'categories', 'brand', 'gender', 'is_active', 'is_featured')
        }),
        ('توضیحات', {
            'fields': ('description', 'short_description')
        }),
        ('قیمت‌گذاری', {
            'fields': ('price', 'discount_percent')
        }),
        ('ویژگی‌های فیزیکی', {
            'fields': ('weight',)
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

    def total_stock(self, obj):
        return obj.total_stock

    total_stock.short_description = "موجودی کل"

    def display_categories(self, obj):
        # ✅ متد کمکی برای نمایش دسته‌بندی‌ها در لیست ادمین
        return ", ".join([category.name for category in obj.categories.all()])

    display_categories.short_description = "دسته‌بندی‌ها"

    def display_image(self, obj):
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
    readonly_fields = ('created_at', 'updated_at')

    def get_products_count(self, obj):
        return obj.get_products_count

    get_products_count.short_description = "تعداد محصولات"

    def display_image(self, obj):
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
    list_display = ['name', 'color_preview']
    search_fields = ['name']
    ordering = ['name']

    def color_preview(self, obj):
        return format_html(
            '<div style="width: 25px; height: 25px; background-color: {}; border-radius: 50%; border: 1px solid #ccc;"></div>',
            obj.hex_code,
        )
    color_preview.short_description = 'پیش‌نمایش'

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ['name', 'id']
    search_fields = ['name']
    ordering = ['name']


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