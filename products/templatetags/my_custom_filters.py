# pages/templatetags/my_custom_filters.py

from django import template

register = template.Library()

@register.filter
def batch(value, arg):
    """
    Returns a list of lists of the given size. For example:
    {% for row in items|batch:3 %}
        {% for item in row %}
            {{ item }}
        {% endfor %}
    {% endfor %}
    """
    try:
        arg = int(arg)
    except ValueError:
        # اگر ورودی arg عدد نبود، لیست اصلی را برمی‌گردانیم
        return value
    if not value:
        return []
    # لیست را به قطعاتی با اندازه arg تقسیم می‌کند
    return [value[i:i + arg] for i in range(0, len(value), arg)]