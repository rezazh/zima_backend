from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification, UserChatStatus


def send_notification(user, title, message, notification_type='system', data=None):
    """ارسال نوتیفیکیشن به کاربر"""
    if data is None:
        data = {}

    # ذخیره نوتیفیکیشن در دیتابیس
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        data=data
    )

    # ارسال از طریق WebSocket اگر کاربر آنلاین باشد
    channel_layer = get_channel_layer()

    try:
        # ارسال به گروه نوتیفیکیشن کاربر
        async_to_sync(channel_layer.group_send)(
            f'notifications_{user.id}',
            {
                'type': 'notification',
                'id': str(notification.id),
                'title': title,
                'message': message,
                'notification_type': notification_type,
                'created_at': notification.created_at.isoformat(),
                'data': data
            }
        )
        return True
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False


def send_chat_notification(room, message_obj):
    """ارسال نوتیفیکیشن برای پیام چت جدید"""
    # ارسال نوتیفیکیشن به همه کاربران اتاق به جز فرستنده پیام
    for user in room.participants.all():
        if user != message_obj.user:
            send_notification(
                user=user,
                title="پیام جدید",
                message=f"پیام جدید از {message_obj.user.get_full_name() or message_obj.user.username}: {message_obj.content[:50]}...",
                notification_type='chat_message',
                data={
                    'room_id': str(room.id),
                    'message_id': str(message_obj.id)
                }
            )
    return True

