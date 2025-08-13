import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.postgres.fields import JSONField


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
        verbose_name = "وضعیت آنلاین کاربر"
        verbose_name_plural = "وضعیت آنلاین کاربران"

    def __str__(self):
        return f"{self.user.username}: {self.get_status_display()}"

    @property
    def is_user_online(self):
        # کاربر در 5 دقیقه گذشته فعالیت داشته باشد، آنلاین در نظر گرفته می‌شود
        if self.status == 'online':
            threshold = timezone.now() - timezone.timedelta(minutes=5)
            return self.last_seen >= threshold
        return False

    def update_status(self):
        """بروزرسانی وضعیت آنلاین بودن کاربر"""
        # بروزرسانی فیلدهای قدیمی برای سازگاری
        self.is_online = self.is_user_online
        self.last_activity = self.last_seen
        self.save(update_fields=['is_online', 'last_activity'])


class ChatRoom(models.Model):
    ROOM_TYPES = [('support', 'Support'), ('general', 'General')]
    STATUS_CHOICES = [('open', 'Open'), ('closed', 'Closed'), ('archived', 'Archived')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,related_name="user_chats")
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_chats"
    )
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='support')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name="closed_chats")
    is_deleted_by_user = models.BooleanField(default=False)
    is_deleted_by_agent = models.BooleanField(default=False)
    hidden_for_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='hidden_chat_rooms',
        blank=True
    )
    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} - {self.user.username}"



class ChatMessage(models.Model):
    MESSAGE_TYPES = [('text', 'Text'), ('image', 'Image'), ('file', 'File'), ('system', 'System')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_messages"
    )
    content = models.TextField()
    file = models.FileField(upload_to='chat_files/%Y/%m/%d/', null=True, blank=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        sender_name = self.sender.username if self.sender else "System"
        return f"{sender_name}: {self.content[:50]}"



class Notification(models.Model):
    """
    مدل اعلان‌های سیستم
    """
    NOTIFICATION_TYPES = [
        ('chat', 'گفتگو'),
        ('system', 'سیستمی'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="کاربر"
    )
    title = models.CharField(max_length=255, verbose_name="عنوان")
    message = models.TextField(verbose_name="متن اعلان")
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='system',
        verbose_name="نوع اعلان"
    )
    data = models.JSONField(default=dict, blank=True, null=True, verbose_name="داده‌های اضافی")
    is_read = models.BooleanField(default=False, verbose_name="خوانده شده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد")

    class Meta:
        verbose_name = "اعلان"
        verbose_name_plural = "اعلان‌ها"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def mark_as_read(self):
        """علامت‌گذاری اعلان به عنوان خوانده شده"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
            return True
        return False


class TemporaryFile(models.Model):
    """
    مدل فایل موقت برای آپلود فایل‌ها قبل از ارسال پیام
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="temp_files",
        verbose_name="کاربر"
    )
    file = models.FileField(upload_to='temp_files/%Y/%m/%d/', verbose_name="فایل")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان آپلود")

    class Meta:
        verbose_name = "فایل موقت"
        verbose_name_plural = "فایل‌های موقت"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.file.name}"