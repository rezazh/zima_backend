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
    """
    مدل اتاق گفتگو بین کاربر و پشتیبان
    """
    ROOM_TYPES = [
        ('support', 'پشتیبانی'),
        ('general', 'عمومی'),
    ]

    STATUS_CHOICES = [
        ('open', 'باز'),
        ('closed', 'بسته شده'),
        ('archived', 'آرشیو شده'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="نام گفتگو")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_chats",
        verbose_name="کاربر"
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_chats",
        verbose_name="پشتیبان"
    )
    room_type = models.CharField(
        max_length=20,
        choices=ROOM_TYPES,
        default='support',
        verbose_name="نوع گفتگو"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name="وضعیت"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان بسته شدن")
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="closed_chats",
        verbose_name="بسته شده توسط"
    )
    is_deleted_by_user = models.BooleanField(default=False, verbose_name="حذف شده توسط کاربر")
    is_deleted_by_agent = models.BooleanField(default=False, verbose_name="حذف شده توسط پشتیبان")
    hidden_for_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='hidden_chat_rooms',
        blank=True,
        help_text='کاربرانی که این گفتگو را حذف کرده‌اند و دیگر نمی‌بینند'
    )
    class Meta:
        verbose_name = "اتاق گفتگو"
        verbose_name_plural = "اتاق‌های گفتگو"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} - {self.user.username}"

    def close(self, user):
        """بستن گفتگو"""
        self.status = 'closed'
        self.closed_at = timezone.now()
        self.closed_by = user
        self.save()

        return True

    def reopen(self, user):
        """بازگشایی گفتگو"""
        if self.status == 'closed':
            self.status = 'open'
            self.closed_at = None
            self.closed_by = None
            self.save()

            return True
        return False

    def archive(self):
        """آرشیو کردن گفتگو"""
        if self.status == 'closed':
            self.status = 'archived'
            self.save()
            return True
        return False

    def mark_deleted_by_user(self):
        """علامت‌گذاری به عنوان حذف شده توسط کاربر"""
        self.is_deleted_by_user = True
        self.save()
        return True

    def mark_deleted_by_agent(self):
        """علامت‌گذاری به عنوان حذف شده توسط پشتیبان"""
        self.is_deleted_by_agent = True
        self.save()
        return True

    @property
    def is_open(self):
        """آیا گفتگو باز است؟"""
        return self.status == 'open'

    @property
    def is_closed(self):
        """آیا گفتگو بسته شده است؟"""
        return self.status == 'closed'

    @property
    def is_archived(self):
        """آیا گفتگو آرشیو شده است؟"""
        return self.status == 'archived'

    @property
    def unread_count_for_user(self):
        """تعداد پیام‌های خوانده نشده برای کاربر"""
        return self.messages.filter(is_read=False, sender=self.agent).count()

    @property
    def unread_count_for_agent(self):
        """تعداد پیام‌های خوانده نشده برای پشتیبان"""
        return self.messages.filter(is_read=False, sender=self.user).count()


class ChatMessage(models.Model):
    """
    مدل پیام گفتگو
    """
    MESSAGE_TYPES = [
        ('text', 'متن'),
        ('image', 'تصویر'),
        ('file', 'فایل'),
        ('system', 'سیستمی'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages", verbose_name="اتاق گفتگو")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_messages",
        verbose_name="فرستنده"
    )
    content = models.TextField(verbose_name="متن پیام")
    file = models.FileField(upload_to='chat_files/%Y/%m/%d/', null=True, blank=True, verbose_name="فایل پیوست")
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPES,
        default='text',
        verbose_name="نوع پیام"
    )
    is_read = models.BooleanField(default=False, verbose_name="خوانده شده")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان خوانده شدن")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ارسال")

    class Meta:
        verbose_name = "پیام گفتگو"
        verbose_name_plural = "پیام‌های گفتگو"
        ordering = ['created_at']

    def __str__(self):
        sender_name = self.sender.username if self.sender else "سیستم"
        return f"{sender_name}: {self.content[:50]}"

    def mark_as_read(self):
        """علامت‌گذاری پیام به عنوان خوانده شده"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
            return True
        return False


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