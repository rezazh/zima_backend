from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
 # لیست همه محصولات - نام‌های مختلف برای سازگاری
 path('', views.product_list, name='list'),
 path('', views.product_list, name='product_list'),

 # نتایج جستجو
 path('search/', views.search_results, name='search'),

 # لیست محصولات بر اساس دسته‌بندی
 path('category/<slug:category_slug>/', views.category_list, name='category_list'),

 # افزودن/حذف محصول از علاقه‌مندی‌ها
 path('toggle-wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
 # path('get-inventory/<int:product_id>/', views.get_inventory_data, name='get_inventory'),

 # افزودن محصول به سبد خرید
 path('add-to-cart/', views.add_to_cart, name='add_to_cart'),

 # افزودن نظر
 path('add-review/<int:product_id>/', views.add_review, name='add_review'),

 # Quick View محصول
 path('<int:product_id>/quick-view/', views.quick_view, name='quick_view'),

 # جزئیات یک محصول خاص - نام‌های مختلف برای سازگاری
 path('<int:product_id>/', views.product_detail, name='detail'),
 path('<int:product_id>/', views.product_detail, name='product_detail'),

    # ⚠️ توجه: توابع زیر در آخرین کد views.py که من برای شما فرستادم، تعریف نشده‌اند.
    # اگر این توابع را در views.py خود ندارید، باید آن‌ها را پیاده‌سازی کنید
    # تا از خطای "AttributeError" جلوگیری شود.
    # path('men/', views.men_products, name='men'),
    # path('women/', views.women_products, name='women'),
    # path('featured/', views.featured_products, name='featured'),
    # path('latest/', views.latest_products, name='latest'),
    # path('<int:product_id>/add-review/', views.add_review, name='add_review'),
]