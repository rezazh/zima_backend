from django import template

register = template.Library()

@register.filter(name='fa_currency')
def fa_currency(value):
    """
    یک مقدار عددی را به رشته‌ای با جداکننده هزارگان و ارقام فارسی تبدیل می‌کند.
    """
    try:
        # تبدیل مقدار به عدد صحیح برای فرمت‌بندی
        value = int(value)
        # استفاده از f-string برای کاماگذاری خودکار بر اساس locale
        return f"{value:,}"
    except (ValueError, TypeError):
        return value