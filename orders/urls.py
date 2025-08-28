from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.order_list, name='list'),
    path('<int:order_id>/', views.order_detail, name='detail'),
    path('cancel/<int:order_id>/', views.cancel_order, name='cancel'),
    path('reorder/<int:order_id>/', views.reorder, name='reorder'),
]