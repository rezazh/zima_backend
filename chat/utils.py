# chat/utils.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from django.utils import timezone


def notify_chat_closed_by_user(room):
    """
    ارسال اطلاع‌رسانی به ادمین مبنی بر بسته شدن چت توسط کاربر
    """
    if not room.admin:
        return

    channel_layer = get_channel_layer()

    # ارسال پیام به گروه چت
    async_to_sync(channel_layer.group_send)(
        f"chat_{room.id}",
        {
            "type": "chat_system_message",
            "event_type": "chat_closed_by_user",
            "message": "این گفتگو توسط کاربر بسته شده است.",
            "timestamp": timezone.now().isoformat(),
        }
    )

    # ارسال اطلاع‌رسانی به ادمین
    async_to_sync(channel_layer.group_send)(
        f"notifications_{room.admin.id}",
        {
            "type": "notification_message",
            "message": f"گفتگو با {room.user.username} توسط کاربر بسته شده است.",
            "title": "بستن گفتگو",
            "data": {
                "chat_id": str(room.id),
                "event_type": "chat_closed_by_user",
            }
        }
    )


def notify_chat_closed_by_admin(room):
    """
    ارسال اطلاع‌رسانی به کاربر مبنی بر بسته شدن چت توسط ادمین
    """
    channel_layer = get_channel_layer()

    # ارسال پیام به گروه چت
    async_to_sync(channel_layer.group_send)(
        f"chat_{room.id}",
        {
            "type": "chat_system_message",
            "event_type": "chat_closed_by_admin",
            "message": "این گفتگو توسط پشتیبانی بسته شده است.",
            "timestamp": timezone.now().isoformat(),
        }
    )

    # ارسال اطلاع‌رسانی به کاربر
    if room.user:
        async_to_sync(channel_layer.group_send)(
            f"notifications_{room.user.id}",
            {
                "type": "notification_message",
                "message": "گفتگوی شما با پشتیبانی بسته شده است.",
                "title": "بستن گفتگو",
                "data": {
                    "chat_id": str(room.id),
                    "event_type": "chat_closed_by_admin",
                }
            }
        )


def notify_chat_reopened(room):
    """
    ارسال اطلاع‌رسانی به کاربر مبنی بر بازگشایی چت
    """
    channel_layer = get_channel_layer()

    # ارسال پیام به گروه چت
    async_to_sync(channel_layer.group_send)(
        f"chat_{room.id}",
        {
            "type": "chat_system_message",
            "event_type": "chat_reopened",
            "message": "این گفتگو بازگشایی شده است.",
            "timestamp": timezone.now().isoformat(),
        }
    )

    # ارسال اطلاع‌رسانی به کاربر
    if room.user:
        async_to_sync(channel_layer.group_send)(
            f"notifications_{room.user.id}",
            {
                "type": "notification_message",
                "message": "گفتگوی شما با پشتیبانی بازگشایی شده است.",
                "title": "بازگشایی گفتگو",
                "data": {
                    "chat_id": str(room.id),
                    "event_type": "chat_reopened",
                }
            }
        )


def create_system_message(room, content):
    """
    ایجاد یک پیام سیستمی در دیتابیس
    """
    from .models import ChatMessage

    # تعیین فرستنده برای پیام سیستمی - ترجیحاً از ادمین استفاده می‌کنیم
    # اگر ادمین وجود نداشت از کاربر استفاده می‌کنیم
    sender = room.admin if room.admin else room.user

    # اگر هیچ کاربری وجود نداشت، از سوپر یوزر استفاده می‌کنیم
    if not sender:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        sender = User.objects.filter(is_superuser=True).first()

        # اگر حتی سوپر یوزر هم وجود نداشت، خطا می‌دهیم
        if not sender:
            raise ValueError("هیچ کاربری برای ارسال پیام سیستمی یافت نشد.")

    message = ChatMessage.objects.create(
        room=room,
        content=content,
        message_type='system',
        is_read=True,  # پیام‌های سیستمی همیشه خوانده شده محسوب می‌شوند
        sender=sender   # تعیین فرستنده برای پیام سیستمی
    )
    return message