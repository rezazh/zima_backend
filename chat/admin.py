from django.contrib import admin
from .models import ChatRoom, ChatMessage, Notification, UserStatus, TemporaryFile


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'agent', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'room_type', 'is_deleted_by_user', 'is_deleted_by_agent')
    search_fields = ('name', 'user__username', 'agent__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('get_short_content', 'room', 'sender', 'message_type', 'is_read', 'created_at')
    list_filter = ('message_type', 'is_read')
    search_fields = ('content', 'room__name', 'sender__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('id', 'created_at')

    def get_short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    get_short_content.short_description = 'محتوا'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('title', 'message', 'user__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('id', 'created_at')


@admin.register(UserStatus)
class UserStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'last_seen')
    list_filter = ('status',)
    search_fields = ('user__username',)
    date_hierarchy = 'last_seen'


@admin.register(TemporaryFile)
class TemporaryFileAdmin(admin.ModelAdmin):
    list_display = ('user', 'file', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'file')
    date_hierarchy = 'created_at'
    readonly_fields = ('id', 'created_at')