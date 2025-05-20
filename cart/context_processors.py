# cart/context_processors.py
def cart_items_count(request):
    """تعداد آیتم‌های سبد خرید را برمی‌گرداند"""
    if request.user.is_authenticated:
        count = request.user.cart_items.count()
    else:
        count = 0

    return {'cart_items_count': count}