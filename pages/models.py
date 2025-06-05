from django.db import models
from django.utils.translation import gettext_lazy as _
from PIL import Image
import os


class Slider(models.Model):
    title = models.CharField(_('عنوان'), max_length=200)
    subtitle = models.CharField(_('زیرعنوان'), max_length=300, blank=True)
    image = models.ImageField(
        _('تصویر'),
        upload_to='sliders/',
        help_text=_('فرمت‌های مجاز: JPG, JPEG, PNG, GIF, WebP')
    )
    link = models.URLField(_('لینک'), blank=True)
    is_active = models.BooleanField(_('فعال'), default=True)
    order = models.PositiveIntegerField(_('ترتیب'), default=0)
    created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاریخ بروزرسانی'), auto_now=True)

    class Meta:
        verbose_name = _('اسلایدر')
        verbose_name_plural = _('اسلایدرها')
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image:
            img_path = self.image.path
            img = Image.open(img_path)

            width, height = img.size
            target_ratio = 16 / 9
            current_ratio = width / height

            if current_ratio > target_ratio:  # تصویر عریض‌تر از نسبت هدف
                new_height = height
                new_width = int(height * target_ratio)
                new_img = Image.new('RGB', (new_width, new_height), (0, 0, 0))
                paste_x = (new_width - width) // 2
                new_img.paste(img, (paste_x, 0))
            elif current_ratio < target_ratio:  # تصویر بلندتر از نسبت هدف
                new_width = width
                new_height = int(width / target_ratio)
                new_img = Image.new('RGB', (new_width, new_height), (0, 0, 0))
                paste_y = (new_height - height) // 2
                new_img.paste(img, (0, paste_y))
            else:
                new_img = img

            new_img.save(img_path, quality=95, optimize=True)