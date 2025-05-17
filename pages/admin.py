# در فایل pages/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Slider

from django.contrib import admin
from django.utils.html import format_html
from .models import Slider


@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'display_image', 'order', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'subtitle')
    list_editable = ('order', 'is_active')
    readonly_fields = ('display_image', 'created_at', 'updated_at')

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'subtitle', 'link')
        }),
        ('تصویر', {
            'fields': ('image', 'display_image')
        }),
        ('تنظیمات نمایش', {
            'fields': ('order', 'is_active')
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def display_image(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" width="200" height="100" style="object-fit: cover;" />', obj.image.url)
        return "بدون تصویر"

    display_image.short_description = "پیش‌نمایش تصویر"

    def make_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} اسلایدر فعال شدند.")

    make_active.short_description = "فعال کردن اسلایدرهای انتخاب شده"

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} اسلایدر غیرفعال شدند.")

    make_inactive.short_description = "غیرفعال کردن اسلایدرهای انتخاب شده"

    def delete_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} اسلایدر با موفقیت حذف شدند.")

    delete_selected.short_description = "حذف اسلایدرهای انتخاب شده"

    actions = ['make_active', 'make_inactive', 'delete_selected']