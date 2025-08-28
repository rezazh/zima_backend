# FILE: products/templatetags/product_filters.py
from django import template
from django.http.request import QueryDict

register = template.Library()

@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """
    Replaces current GET parameters with new ones provided in kwargs.
    Useful for pagination and sorting.
    Example: {% url_replace page=products.next_page_number sort='price_low' %}
    """
    query = context['request'].GET.copy()
    for key, value in kwargs.items():
        if value is None:
            if key in query:
                del query[key]
        else:
            query[key] = value
    return query.urlencode()

@register.filter
def get_item(dictionary, key):
    """
    Allows accessing dictionary items by key in Django templates.
    Example: {{ my_dict|get_item:key_variable }}
    """
    return dictionary.get(key)

@register.filter
def is_string(value):
    return isinstance(value, str)

@register.filter
def is_number(value):
    return isinstance(value, (int, float))

@register.filter
def is_list(value):
    return isinstance(value, list)

@register.filter
def is_queryset(value):
    from django.db.models.query import QuerySet
    return isinstance(value, QuerySet)