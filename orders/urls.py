from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartItemViewSet, CheckoutView, OrderHistoryView, update_order_status

router = DefaultRouter()
router.register(r'cart', CartItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('orders/', OrderHistoryView.as_view(), name='order-history'),
    path('orders/<int:order_id>/status/', update_order_status, name='update-order-status'),

]