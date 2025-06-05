# chat/admin.py
from django.contrib import admin
from .models import ChatRoom, ChatMessage, UserChatStatus, Notification


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'room_type', 'is_active', 'created_at')
    list_filter = ('room_type', 'is_active')
    search_fields = ('name',)
    filter_horizontal = ('participants',)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'room', 'message_type', 'content_preview', 'created_at')
    list_filter = ('message_type', 'is_read')
    search_fields = ('content',)

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    content_preview.short_description = 'محتوا'


@admin.register(UserChatStatus)
class UserChatStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'last_seen', 'is_staff_available')
    list_filter = ('status', 'is_staff_available')
    search_fields = ('user__username',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('title', 'message')