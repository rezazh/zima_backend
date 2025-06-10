# chat/urls.py
from django.urls import path
from . import views
from .views import SetUserOfflineView, SetUserOnlineView

app_name = 'chat'

urlpatterns = [
    path('', views.chat_list, name='chat_list'),
    path('start/', views.start_chat, name='start_chat'),
    path('room/<uuid:room_id>/', views.chat_room, name='chat_room'),
    path('support/create/', views.create_support_chat, name='create_support_chat'),
    path('api/user-closed-chats/', views.api_user_closed_chats, name='api_user_closed_chats'),

    # اصلاح مسیر notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<uuid:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/count/', views.notification_count, name='notification_count'),

    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('assign-admin/<uuid:room_id>/', views.assign_admin, name='assign_admin'),
    path('close/<uuid:room_id>/', views.close_chat, name='close_chat'),
    path('reopen/<uuid:room_id>/', views.reopen_chat, name='reopen_chat'),
    path('delete/<uuid:room_id>/', views.delete_chat, name='delete_chat'),
    path('mark-read/<int:message_id>/', views.mark_message_as_read, name='mark_message_as_read'),

    path('api/pending-chats/', views.api_pending_chats, name='api_pending_chats'),
    path('api/active-chats/', views.api_active_chats, name='api_active_chats'),
    path('api/unread-counts/', views.api_unread_counts, name='api_unread_counts'),
    path('set-online/', views.SetUserOnlineView.as_view(), name='set_online_status'),
    path('set-offline/', views.SetUserOfflineView.as_view(), name='set_offline_status'),
    path('unread-count/', views.unread_count, name='unread_count'),
    path('user-status/<int:user_id>/', views.get_user_status, name='get_user_status'),
    path('user-close/<uuid:room_id>/', views.user_close_chat, name='user_close_chat'),
    path('admin-close/<uuid:room_id>/', views.admin_close_chat, name='admin_close_chat'),
    path('archive/<uuid:room_id>/', views.archive_chat, name='archive_chat'),
]