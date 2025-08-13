import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class UserStatus(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='online_status'
    )
    is_online = models.BooleanField(default=False)
    last_activity = models.DateTimeField(null=True, blank=True)
    typing_in_room = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=[('online', 'Online'), ('offline', 'Offline')],
        default='offline'
    )
    last_seen = models.DateTimeField(default=timezone.now)
    last_heartbeat = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "User Online Status"
        verbose_name_plural = "User Online Statuses"

    def __str__(self):
        return f"{self.user.username}: {self.get_status_display()}"


class ChatRoom(models.Model):
    ROOM_TYPES = [('support', 'Support'), ('general', 'General')]
    STATUS_CHOICES = [('open', 'Open'), ('closed', 'Closed'), ('archived', 'Archived')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_chats")
    agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="agent_chats")
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='support')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="closed_chats")
    is_deleted_by_user = models.BooleanField(default=False)
    is_deleted_by_agent = models.BooleanField(default=False)
    hidden_for_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='hidden_chat_rooms', blank=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Chat Room"
        verbose_name_plural = "Chat Rooms"

    def __str__(self):
        return f"{self.name} - {self.user.username}"

    # ===== RESTORED METHODS START HERE =====
    def close(self, user):
        self.status = 'closed'
        self.closed_at = timezone.now()
        self.closed_by = user
        self.save()
        return True

    def reopen(self, user):
        if self.status == 'closed':
            self.status = 'open'
            self.closed_at = None
            self.closed_by = None
            self.save()
            return True
        return False

    def archive(self):
        if self.status == 'closed':
            self.status = 'archived'
            self.save()
            return True
        return False

    def mark_deleted_by_user(self):
        self.is_deleted_by_user = True
        self.save()
        return True

    def mark_deleted_by_agent(self):
        self.is_deleted_by_agent = True
        self.save()
        return True
    # ===== RESTORED METHODS END HERE =====

    @property
    def is_open(self):
        return self.status == 'open'

    @property
    def is_closed(self):
        return self.status == 'closed'

    @property
    def is_archived(self):
        return self.status == 'archived'

    @property
    def unread_count_for_user(self):
        if self.agent:
            return self.messages.filter(is_read=False, sender=self.agent).count()
        return 0

    @property
    def unread_count_for_agent(self):
        return self.messages.filter(is_read=False, sender=self.user).count()


class ChatMessage(models.Model):
    MESSAGE_TYPES = [('text', 'Text'), ('image', 'Image'), ('file', 'File'), ('system', 'System')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_messages")
    content = models.TextField()
    file = models.FileField(upload_to='chat_files/%Y/%m/%d/', null=True, blank=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self):
        sender_name = self.sender.username if self.sender else "System"
        return f"{sender_name}: {self.content[:50]}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
            return True
        return False

class Notification(models.Model):

    NOTIFICATION_TYPES = [('chat', 'Chat'), ('system', 'System')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    data = models.JSONField(default=dict, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class TemporaryFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="temp_files")
    file = models.FileField(upload_to='temp_files/%Y/%m/%d/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Temporary File"
        verbose_name_plural = "Temporary Files"

    def __str__(self):
        return f"{self.user.username} - {self.file.name}"