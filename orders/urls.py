from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('payment/<int:order_id>/', views.payment, name='payment'),
    path('confirmation/<int:order_id>/', views.order_confirmation, name='confirmation'),
    path('list/', views.order_list, name='list'),
    path('detail/<int:order_id>/', views.order_detail, name='detail'),
]