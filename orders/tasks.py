from django.utils.timezone import now

from cart.models import CartItem


def delete_expired_cart_items():
    expired_items = CartItem.objects.filter(expires_at__lt=now())
    expired_items.delete()