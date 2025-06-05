import os

from django.db import models
from django.conf import settings  # برای دسترسی به AUTH_USER_MODEL
from django.utils import timezone
import uuid


class ChatRoom(models.Model):
    """اتاق چت"""
    ROOM_TYPES = [
        ('support', 'پشتیبانی'),
        ('general', 'عمومی'),
        ('private', 'خصوصی'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('نام اتاق', max_length=100)
    room_type = models.CharField('نوع اتاق', max_length=20, choices=ROOM_TYPES, default='support')
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_rooms', blank=True)
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)
    updated_at = models.DateTimeField('تاریخ بروزرسانی', auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_chat_rooms', null=True, blank=True)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_chat_rooms', null=True, blank=True)

    class Meta:
        verbose_name = 'اتاق چت'
        verbose_name_plural = 'اتاق‌های چت'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()})"

    @property
    def group_name(self):
        """نام گروه برای channels"""
        return f'chat_{self.id}'


class ChatMessage(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('system', 'System'),
    ]

    # id فعلی را حفظ کنید (تغییر ندهید)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    file_size = models.IntegerField(null=True, blank=True)  # در بایت
    file_type = models.CharField(max_length=50, null=True, blank=True)  # مثلا image/jpeg یا application/pdf
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default='text')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"

    def save(self, *args, **kwargs):
        # اگر فایل آپلود شده و نوع پیام مشخص نشده، نوع پیام را تعیین کن
        if self.file and (not self.message_type or self.message_type == 'text'):
            file_ext = os.path.splitext(self.file.name)[1].lower()
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']

            if file_ext in image_extensions:
                self.message_type = 'image'
            else:
                self.message_type = 'file'

            # ذخیره نام فایل و سایز آن
            if not self.file_name:
                self.file_name = os.path.basename(self.file.name)

            # سایز فایل را ذخیره کن
            if not self.file_size and hasattr(self.file, 'size'):
                self.file_size = self.file.size

            # نوع فایل را ذخیره کن
            if not self.file_type:
                import mimetypes
                self.file_type = mimetypes.guess_type(self.file.name)[0] or 'application/octet-stream'

        super().save(*args, **kwargs)


class UserChatStatus(models.Model):
    """وضعیت آنلاین کاربران"""
    STATUS_CHOICES = [
        ('online', 'آنلاین'),
        ('away', 'غایب'),
        ('busy', 'مشغول'),
        ('offline', 'آفلاین'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_status')
    status = models.CharField('وضعیت', max_length=20, choices=STATUS_CHOICES, default='offline')
    last_seen = models.DateTimeField('آخرین بازدید', auto_now=True)
    is_staff_available = models.BooleanField('ادمین در دسترس', default=False)

    class Meta:
        verbose_name = 'وضعیت چت کاربر'
        verbose_name_plural = 'وضعیت چت کاربران'

    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"


class Notification(models.Model):
    """نوتیفیکیشن‌ها"""
    NOTIFICATION_TYPES = [
        ('chat', 'پیام چت'),
        ('order', 'بروزرسانی سفارش'),
        ('product', 'موجود شدن محصول'),
        ('system', 'سیستم'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField('نوع نوتیفیکیشن', max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField('عنوان', max_length=200)
    message = models.TextField('پیام')
    data = models.JSONField('داده‌های اضافی', default=dict, blank=True)
    is_read = models.BooleanField('خوانده شده', default=False)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'نوتیفیکیشن'
        verbose_name_plural = 'نوتیفیکیشن‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"


class DeletedChat(models.Model):
    """مدل برای ذخیره چت‌هایی که کاربر حذف کرده است"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='del_messages')
    deleted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'room')

    def __str__(self):
        return f"{self.user.username} deleted chat {self.room.id}"