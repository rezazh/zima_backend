from django.urls import path
from . import views
from products import views as products_views # ✅ این خط را اضافه کنید

app_name = 'cart'

urlpatterns = [
    # تغییر نام route اصلی
    path('', views.cart_summary, name='cart'),  # تغییر از 'summary' به 'cart'
    path('summary/', views.cart_summary, name='summary'),  # نگه داشتن route قدیمی برای سازگاری

    # اضافه کردن توابع جدید
    path('add/', products_views.add_to_cart, name='add_to_cart'),
    path('update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('clear/', views.clear_cart, name='clear_cart'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),  # اضافه شده
    path('save-for-later/<int:item_id>/', views.save_for_later, name='save_for_later'),  # اضافه شده
]