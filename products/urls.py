from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('<int:product_id>/', views.product_detail, name='detail'),
    path('category/<slug:category_slug>/', views.category_products, name='category'),
    path('men/', views.men_products, name='men'),
    path('women/', views.women_products, name='women'),
    path('featured/', views.featured_products, name='featured'),
    path('latest/', views.latest_products, name='latest'),
    path('<int:product_id>/add-review/', views.add_review, name='add_review'),
]