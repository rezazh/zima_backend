from .models import CartItem

def cart_count(request):
    """تعداد محصولات سبد خرید برای نمایش در هدر"""
    if request.user.is_authenticated:
        count = CartItem.objects.filter(user=request.user).count()
        return {'cart_count': count}
    return {'cart_count': 0}