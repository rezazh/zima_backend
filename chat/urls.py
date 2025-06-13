from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # صفحات اصلی چت
    path('', views.chat_list, name='chat_list'),
    path('room/<uuid:room_id>/', views.chat_room, name='room'),
    path('start/', views.start_chat, name='start'),

    # صفحات مدیریت
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/assign/<uuid:room_id>/', views.assign_room, name='assign_room'),

    # اعلان‌ها
    path('notifications/', views.notifications_view, name='notifications'),

    # API‌های چت
    path('api/mark-read/<uuid:message_id>/', views.mark_message_read, name='mark_read'),
    path('api/close-room/<uuid:room_id>/', views.close_room, name='close_room'),
    path('api/reopen-room/<uuid:room_id>/', views.reopen_room, name='reopen_room'),
    path('api/upload-file/', views.upload_temp_file, name='upload_file'),

    # API‌های وضعیت آنلاین
    path('set-online/', views.set_online, name='set_online'),
    path('set-offline/', views.set_offline, name='set_offline'),
    path('unread-count/', views.get_unread_count, name='unread_count'),
    path('hide-room/<uuid:room_id>/', views.hide_room, name='hide_room'),

]