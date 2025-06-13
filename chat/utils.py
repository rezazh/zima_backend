from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def create_system_message(room, content):
    """
    ایجاد یک پیام سیستمی در دیتابیس
    """
    from .models import ChatMessage

    # ایجاد پیام سیستمی بدون فرستنده
    message = ChatMessage.objects.create(
        room=room,
        content=content,
        message_type='system',
        sender=None,  # پیام سیستمی بدون فرستنده
        is_read=True  # پیام‌های سیستمی همیشه خوانده شده محسوب می‌شوند
    )

    # ارسال رویداد به کانال
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{room.id}',
            {
                'type': 'chat_message',
                'message': {
                    'id': str(message.id),
                    'content': message.content,
                    'message_type': message.message_type,
                    'created_at': message.created_at.isoformat(),
                    'is_system': True
                }
            }
        )
    except Exception as e:
        print(f"Error sending system message to channel: {e}")

    return message


def notify_chat_closed_by_user(room):
    """
    اطلاع‌رسانی به ادمین درباره بسته شدن چت توسط کاربر
    """
    if room.admin:
        from .models import Notification

        # ایجاد نوتیفیکیشن برای ادمین
        Notification.objects.create(
            user=room.admin,
            title="بستن چت",
            message=f"کاربر {room.user.username} چت را بسته است.",
            notification_type="chat",
            data={
                'room_id': str(room.id),
                'action': 'closed_by_user'
            },
            is_read=False
        )

        # ارسال نوتیفیکیشن از طریق وب‌سوکت
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'notifications_{room.admin.id}',
                {
                    'type': 'notification_message',
                    'title': "بستن چت",
                    'message': f"کاربر {room.user.username} چت را بسته است.",
                    'data': {
                        'room_id': str(room.id),
                        'action': 'closed_by_user'
                    }
                }
            )
        except Exception as e:
            print(f"Error sending notification to admin: {e}")


def notify_chat_closed_by_admin(room):
    """
    اطلاع‌رسانی به کاربر درباره بسته شدن چت توسط ادمین
    """
    if room.user:
        from .models import Notification

        admin_name = room.admin.get_full_name() if room.admin and room.admin.get_full_name() else "پشتیبانی"

        # ایجاد نوتیفیکیشن برای کاربر
        Notification.objects.create(
            user=room.user,
            title="بستن چت",
            message=f"{admin_name} چت را بسته است.",
            notification_type="chat",
            data={
                'room_id': str(room.id),
                'action': 'closed_by_admin'
            },
            is_read=False
        )

        # ارسال نوتیفیکیشن از طریق وب‌سوکت
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'notifications_{room.user.id}',
                {
                    'type': 'notification_message',
                    'title': "بستن چت",
                    'message': f"{admin_name} چت را بسته است.",
                    'data': {
                        'room_id': str(room.id),
                        'action': 'closed_by_admin'
                    }
                }
            )
        except Exception as e:
            print(f"Error sending notification to user: {e}")


def notify_chat_reopened(room):
    """
    اطلاع‌رسانی به کاربر درباره بازگشایی چت
    """
    if room.user:
        from .models import Notification

        admin_name = room.admin.get_full_name() if room.admin and room.admin.get_full_name() else "پشتیبانی"

        # ایجاد نوتیفیکیشن برای کاربر
        Notification.objects.create(
            user=room.user,
            title="بازگشایی چت",
            message=f"{admin_name} چت را بازگشایی کرده است.",
            notification_type="chat",
            data={
                'room_id': str(room.id),
                'action': 'reopened'
            },
            is_read=False
        )

        # ارسال نوتیفیکیشن از طریق وب‌سوکت
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'notifications_{room.user.id}',
                {
                    'type': 'notification_message',
                    'title': "بازگشایی چت",
                    'message': f"{admin_name} چت را بازگشایی کرده است.",
                    'data': {
                        'room_id': str(room.id),
                        'action': 'reopened'
                    }
                }
            )
        except Exception as e:
            print(f"Error sending notification to user: {e}")