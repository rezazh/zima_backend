from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('terms/', views.terms, name='terms'),
    path('newsletter/', views.newsletter, name='newsletter'),
    path('privacy/', views.privacy, name='privacy'),
    path('returns/', views.returns, name='returns'),
    path('size-guide/', views.size_guide_view, name='size-guide'),
    path('shopping-guide/', views.shopping_guide_view, name='shopping_guide'),
    path('shipping-conditions/', views.shipping_conditions_view, name='shipping_conditions'),
    path('shipping/', views.shipping, name='shipping'),
    path('product-quality/', views.product_quality_view, name='product_quality'),
    path('returns-policy/', views.returns_policy_view, name='returns_policy'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),

]
