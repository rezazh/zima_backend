from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet, featured_products, similar_products, add_product, add_Category, \
    latest_products, women_underwear_products, men_underwear_products, men_products, get_filter_options, product_detail

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'categories', CategoryViewSet, basename='category')


urlpatterns = [
    path('', include(router.urls)),
    path('products/featured/', featured_products, name='featured-products'),
    path('products/<int:product_id>/similar/', similar_products, name='similar-products'),
    path('add/products/', add_product, name='add_product'),
    path('add/category/', add_Category, name='add_Category'),
    path('latest/', latest_products, name='latest-products'),
    path('women-underwear/', women_underwear_products, name='women-underwear-products'),
    path('men-underwear/', men_underwear_products, name='men-underwear-products'),
    path('men/', men_products, name='men-products'),
    path('filter-options/', get_filter_options, name='filter-options'),
    path('product/<int:product_id>/', product_detail, name='product-detail'),

]