from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import ChatMessage, ChatRoom, Notification, UserStatus
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

# متغیرهای کنترل برای جلوگیری از حلقه بی‌نهایت
updating_room = False
creating_system_message = False
User = get_user_model()



@receiver(post_save, sender=User)
def create_user_status(sender, instance, created, **kwargs):
    """ایجاد وضعیت آنلاین برای کاربران جدید"""
    if created:
        UserStatus.objects.create(user=instance, status='offline')


@receiver(post_save, sender=ChatMessage)
def message_post_save(sender, instance, created, **kwargs):
    """
    به‌روزرسانی زمان آخرین فعالیت اتاق گفتگو پس از ذخیره پیام جدید
    """
    global updating_room

    # اگر در حال به‌روزرسانی اتاق هستیم، از ادامه جلوگیری می‌کنیم
    if updating_room:
        return

    try:
        room = instance.room

        # علامت‌گذاری به‌روزرسانی اتاق
        updating_room = True

        # به‌روزرسانی زمان آخرین فعالیت اتاق
        room.updated_at = timezone.now()
        room.save(update_fields=['updated_at'])
    finally:
        # بازنشانی متغیر
        updating_room = False

    # ارسال اعلان به کاربر مقابل
    if created and instance.sender and instance.message_type != 'system':
        room = instance.room

        # تعیین گیرنده اعلان (کاربر مقابل فرستنده)
        recipient = None
        if instance.sender == room.user and room.agent:
            recipient = room.agent
        elif instance.sender == room.agent and room.user:
            recipient = room.user

        if recipient:
            # ایجاد اعلان
            Notification.objects.create(
                user=recipient,
                title="پیام جدید",
                message=f"پیام جدید از {instance.sender.username}: {instance.content[:50]}{'...' if len(instance.content) > 50 else ''}",
                notification_type="chat",
                data={
                    "room_id": str(room.id),
                    "message_id": str(instance.id)
                }
            )


@receiver(pre_save, sender=ChatRoom)
def room_pre_save(sender, instance, **kwargs):
    """
    ایجاد پیام سیستمی در صورت تغییر وضعیت اتاق گفتگو
    """
    global creating_system_message

    if creating_system_message:
        return

    # بررسی تغییر وضعیت اتاق
    if not instance._state.adding:  # اگر در حال ویرایش است (نه ایجاد جدید)
        try:
            old_instance = ChatRoom.objects.get(pk=instance.pk)

            # تغییر وضعیت از باز به بسته
            if old_instance.status == 'open' and instance.status == 'closed':
                creating_system_message = True

                try:
                    # ایجاد پیام سیستمی با بررسی closed_by
                    message = "این گفتگو توسط پشتیبانی بسته شده است." if instance.closed_by and instance.closed_by.is_staff else "این گفتگو توسط کاربر بسته شده است."
                    ChatMessage.objects.create(
                        room=instance,
                        content=message,
                        message_type="system"
                    )
                finally:
                    creating_system_message = False

            # تغییر وضعیت از بسته به باز
            elif old_instance.status == 'closed' and instance.status == 'open':
                creating_system_message = True

                try:
                    # ایجاد پیام سیستمی
                    message = "این گفتگو توسط پشتیبانی بازگشایی شده است." if instance.closed_by and instance.closed_by.is_staff else "این گفتگو توسط کاربر بازگشایی شده است."
                    ChatMessage.objects.create(
                        room=instance,
                        content=message,
                        message_type="system"
                    )
                finally:
                    creating_system_message = False
        except ChatRoom.DoesNotExist:
            pass  # اتاق جدید است


@receiver(post_save, sender=Notification)
def notification_post_save(sender, instance, created, **kwargs):
    """
    ارسال اعلان جدید به کاربر از طریق WebSocket
    """
    if created:
        # ارسال اعلان به کانال کاربر
        channel_layer = get_channel_layer()

        # تهیه داده‌های اعلان برای ارسال
        notification_data = {
            'type': 'notification_message',
            'notification': {
                'id': str(instance.id),
                'title': instance.title,
                'message': instance.message,
                'notification_type': instance.notification_type,
                'is_read': instance.is_read,
                'created_at': instance.created_at.isoformat(),
                'data': instance.data
            }
        }

        # ارسال به گروه کاربر
        try:
            async_to_sync(channel_layer.group_send)(
                f'notifications_{instance.user.id}',
                notification_data
            )
        except:
            pass  # اگر کاربر آنلاین نباشد، خطا نادیده گرفته می‌شود