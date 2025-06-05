from django.contrib.auth import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import UserChatStatus, ChatRoom

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_chat_status(sender, instance, created, **kwargs):
    """ایجاد وضعیت چت برای کاربران جدید"""
    if created:
        UserChatStatus.objects.create(user=instance)


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """تغییر وضعیت کاربر به آنلاین هنگام ورود"""
    try:
        status, created = UserChatStatus.objects.get_or_create(user=user)
        status.status = 'online'
        status.save()

        # اطلاع‌رسانی به اتاق‌های چت کاربر
        notify_status_change(user, 'online')
    except Exception as e:
        print(f"Error updating user status on login: {e}")


@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """تغییر وضعیت کاربر به آفلاین هنگام خروج"""
    if user and not user.is_anonymous:
        try:
            status = UserChatStatus.objects.filter(user=user).first()
            if status:
                status.status = 'offline'
                status.save()

                # اطلاع‌رسانی به اتاق‌های چت کاربر
                notify_status_change(user, 'offline')
        except Exception as e:
            print(f"Error updating user status on logout: {e}")


def notify_status_change(user, status):
    """اطلاع‌رسانی تغییر وضعیت کاربر به اتاق‌های چت مرتبط"""
    try:
        channel_layer = get_channel_layer()

        # دریافت تمام اتاق‌های چت کاربر
        if user.is_staff:
            chat_rooms = ChatRoom.objects.filter(admin=user)
        else:
            chat_rooms = ChatRoom.objects.filter(user=user)

        # ارسال اطلاعیه به هر اتاق
        for room in chat_rooms:
            async_to_sync(channel_layer.group_send)(
                f'chat_{room.id}',
                {
                    'type': 'user_status_update',
                    'user_id': user.id,
                    'username': user.username,
                    'status': status,
                    'is_staff': user.is_staff
                }
            )

        # همچنین اطلاع‌رسانی به کانال اعلان‌های کاربر برای بروزرسانی آیکن وضعیت
        notification_group = f'notifications_{user.id}'
        async_to_sync(channel_layer.group_send)(
            notification_group,
            {
                'type': 'user_status_update',
                'user_id': user.id,
                'username': user.username,
                'status': status,
                'is_staff': user.is_staff
            }
        )
    except Exception as e:
        print(f"Error notifying status change: {e}")