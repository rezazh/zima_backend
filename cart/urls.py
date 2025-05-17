from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_summary, name='summary'),
    path('add/<int:product_id>/', views.add_to_cart, name='add'),
    path('update/<int:item_id>/', views.update_cart, name='update'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove'),
    path('clear/', views.clear_cart, name='clear'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
]