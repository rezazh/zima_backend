# cart/context_processors.py
from products.models import Banner


def cart_items_count(request):
    """تعداد آیتم‌های سبد خرید را برمی‌گرداند"""
    if request.user.is_authenticated:
        count = request.user.cart_items.count()
    else:
        count = 0

    return {'cart_items_count': count}

def banners(request):
    """اضافه کردن بنرها به تمام صفحات"""
    return {
        'global_top_banners': Banner.objects.filter(position='home_top', is_active=True).order_by('order'),
        'global_middle_banners': Banner.objects.filter(position='home_middle', is_active=True).order_by('order'),
        'global_bottom_banners': Banner.objects.filter(position='home_bottom', is_active=True).order_by('order'),
    }