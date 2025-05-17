from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, ProductFeature, Review, Tag, Banner


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'get_products_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
    'name', 'display_image', 'category', 'brand', 'price', 'discount_percent', 'stock', 'is_active', 'is_featured',
    'created_at')
    list_filter = ('is_active', 'is_featured', 'category', 'brand', 'gender', 'created_at')
    search_fields = ('name', 'description', 'short_description', 'brand')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'discount_percent', 'stock', 'is_active', 'is_featured')
    readonly_fields = ('created_at', 'updated_at', 'total_sales', 'display_image')
    inlines = [ProductImageInline, ProductFeatureInline]
    actions = ['make_active', 'make_inactive', 'delete_selected']

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'slug', 'category', 'brand', 'gender')
        }),
        ('توضیحات', {
            'fields': ('description', 'short_description')
        }),
        ('قیمت و موجودی', {
            'fields': ('price', 'discount_percent', 'stock', 'is_active', 'is_featured')
        }),
        ('مشخصات فیزیکی', {
            'fields': ('sizes', 'colors', 'color_codes', 'weight', 'dimensions')
        }),
        ('سئو', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('تصویر', {
            'fields': ('display_image',)
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_at', 'updated_at', 'total_sales'),
            'classes': ('collapse',)
        }),
    )

    def make_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} محصول فعال شدند.")

    make_active.short_description = "فعال کردن محصولات انتخاب شده"

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} محصول غیرفعال شدند.")

    make_inactive.short_description = "غیرفعال کردن محصولات انتخاب شده"

    def display_image(self, obj):
        main_image = obj.get_main_image()
        if main_image and main_image.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                               main_image.image.url)
        return "بدون تصویر"

    display_image.short_description = "تصویر"



    def delete_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} محصول با موفقیت حذف شدند.")

    delete_selected.short_description = "حذف محصولات انتخاب شده"

    class Media:
        js = ('js/admin/confirm_delete.js',)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'alt_text', 'is_main', 'created_at')
    list_filter = ('is_main', 'created_at')
    search_fields = ('product__name', 'alt_text')
    list_editable = ('is_main',)
    raw_id_fields = ('product',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')
    list_editable = ('is_approved',)
    raw_id_fields = ('product', 'user')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('products',)


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'display_image', 'position', 'order', 'is_active', 'start_date', 'end_date')
    list_filter = ('position', 'is_active', 'created_at')
    search_fields = ('title', 'subtitle')
    list_editable = ('position', 'order', 'is_active')
    readonly_fields = ('display_image',)

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="50" style="object-fit: cover;" />', obj.image.url)
        return "بدون تصویر"

    display_image.short_description = "پیش‌نمایش"

