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

    path('shipping/', views.shipping, name='shipping'),
]
