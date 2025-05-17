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

        # بعد از ذخیره، تصویر را ریسایز کن
        if self.image:
            img_path = self.image.path
            img = Image.open(img_path)

            # اگر تصویر بزرگتر از سایز مورد نظر است، آن را ریسایز کن
            max_width = 1920
            max_height = 800

            if img.width > max_width or img.height > max_height:
                # حفظ نسبت ابعاد
                if img.width / img.height > max_width / max_height:
                    # تصویر عریض‌تر است
                    new_width = max_width
                    new_height = int(img.height * (max_width / img.width))
                else:
                    # تصویر بلندتر است
                    new_height = max_height
                    new_width = int(img.width * (max_height / img.height))

                # ریسایز تصویر
                img = img.resize((new_width, new_height), Image.LANCZOS)

                # ذخیره مجدد تصویر
                img.save(img_path, quality=85)