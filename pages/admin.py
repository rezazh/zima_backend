# در فایل pages/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Slider

from django.contrib import admin
from django.utils.html import format_html
from .models import Slider


@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'thumbnail', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('title', 'subtitle')
    readonly_fields = ('preview_image',)

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'subtitle', 'link')
        }),
        ('تصویر', {
            'fields': ('image', 'preview_image'),
            'description': 'برای بهترین نتیجه، تصویری با نسبت 16:9 (مثلاً 1920×1080) و کیفیت بالا آپلود کنید.'
        }),
        ('تنظیمات نمایش', {
            'fields': ('order', 'is_active')
        }),
    )

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" style="max-height: 60px; width: auto;" />', obj.image.url)
        return "بدون تصویر"

    thumbnail.short_description = "تصویر"

    def preview_image(self, obj):
        if obj.image:
            # نمایش تصویر با اندازه واقعی و مقیاس مناسب (بدون برش)
            return format_html('''
                <div style="margin-top: 10px; margin-bottom: 10px;">
                    <img src="{}" style="max-width: 100%; max-height: 400px; width: auto; height: auto;" />
                    <p style="margin-top: 5px; color: #666;">ابعاد تصویر: {}x{} پیکسل</p>
                </div>
            ''', obj.image.url, obj.image.width, obj.image.height)
        return "تصویری انتخاب نشده است."

    preview_image.short_description = "پیش‌نمایش تصویر (اندازه واقعی)"