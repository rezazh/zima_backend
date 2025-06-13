# chat/services.py
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

from .models import ChatRoom, ChatMessage, Notification, UserStatus


class UserStatusService:
    """سرویس مدیریت وضعیت آنلاین/آفلاین کاربران"""

    @staticmethod
    def set_user_status(user, status):
        """تنظیم وضعیت کاربر و ارسال به‌روزرسانی به همه کاربران"""
        if not user or not user.is_authenticated:
            return None

        # به‌روزرسانی یا ایجاد وضعیت کاربر در دیتابیس
        user_status, created = UserStatus.objects.update_or_create(
            user=user,
            defaults={
                'status': status,
                'last_seen': timezone.now()
            }
        )

        # ارسال به‌روزرسانی به همه کاربران از طریق وب‌سوکت
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "online_status",
            {
                'type': 'online_status_update',
                'user_id': str(user.id),
                'status': status
            }
        )

        return user_status

    @staticmethod
    def update_last_seen(user):
        """به‌روزرسانی زمان آخرین فعالیت کاربر"""
        if not user or not user.is_authenticated:
            return None

        user_status, created = UserStatus.objects.update_or_create(
            user=user,
            defaults={
                'last_seen': timezone.now()
            }
        )

        return user_status

    @staticmethod
    def get_user_status(user):
        """دریافت وضعیت کاربر"""
        if not user or not user.is_authenticated:
            return 'offline'

        try:
            user_status = UserStatus.objects.get(user=user)
            return user_status.status
        except UserStatus.DoesNotExist:
            return 'offline'

    @staticmethod
    def get_all_online_users():
        """دریافت لیست تمام کاربران آنلاین"""
        threshold = timezone.now() - timezone.timedelta(minutes=5)
        return UserStatus.objects.filter(
            status='online',
            last_seen__gte=threshold
        ).select_related('user')

class ChatService:
    @staticmethod
    def create_room(user, name=None):
        """
        ایجاد اتاق گفتگوی جدید
        """
        if not name:
            name = f"گفتگو با {user.get_full_name() or user.username}"

        room = ChatRoom.objects.create(
            user=user,
            name=name,
            status='open'
        )

        return room

    @staticmethod
    def close_room(room, user):
        """
        بستن اتاق گفتگو
        """
        if room.status != 'open':
            return False

        room.status = 'closed'
        room.closed_at = timezone.now()

        # تعیین کاربری که گفتگو را بسته است
        if user.is_staff:
            room.is_closed_by_admin = True

        room.save()

        # ارسال پیام به کانال وب‌سوکت
        channel_layer = get_channel_layer()
        room_group_name = f'chat_{room.id}'

        message = "این گفتگو توسط پشتیبانی بسته شده است." if user.is_staff else "این گفتگو توسط کاربر بسته شده است."

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'type': 'chat_closed',
                    'message': message,
                    'closed_by': user.id,
                    'is_staff': user.is_staff,
                    'closed_at': timezone.now().isoformat()
                }
            }
        )

        return True

    @staticmethod
    def reopen_room(room, user):
        """
        بازگشایی اتاق گفتگو
        """
        if room.status != 'closed':
            return False

        room.status = 'open'
        room.closed_at = None
        room.is_closed_by_admin = False
        room.save()

        # ارسال پیام به کانال وب‌سوکت
        channel_layer = get_channel_layer()
        room_group_name = f'chat_{room.id}'

        message = "این گفتگو بازگشایی شده است."

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'type': 'chat_reopened',
                    'message': message,
                    'reopened_by': user.id,
                    'is_staff': user.is_staff,
                    'reopened_at': timezone.now().isoformat()
                }
            }
        )

        return True

    @staticmethod
    def archive_room(room):
        """
        آرشیو کردن اتاق گفتگو
        """
        if room.status != 'closed':
            return False

        room.status = 'archived'
        room.save()

        return True

    @staticmethod
    def create_message(room, sender, content, message_type='text', file=None):
        """
        ایجاد پیام جدید
        """
        message = ChatMessage.objects.create(
            room=room,
            sender=sender,
            content=content,
            message_type=message_type,
            file=file
        )

        # بروزرسانی زمان آخرین فعالیت اتاق
        room.updated_at = timezone.now()
        room.save(update_fields=['updated_at'])

        return message

    @staticmethod
    def create_system_message(room, content):
        """
        ایجاد پیام سیستمی
        """
        message = ChatMessage.objects.create(
            room=room,
            content=content,
            message_type='system'
        )

        # بروزرسانی زمان آخرین فعالیت اتاق
        room.updated_at = timezone.now()
        room.save(update_fields=['updated_at'])

        return message

    @staticmethod
    def mark_message_as_read(message):
        """
        علامت‌گذاری پیام به عنوان خوانده شده
        """
        if not message.is_read:
            message.is_read = True
            message.read_at = timezone.now()
            message.save(update_fields=['is_read', 'read_at'])

            # ارسال پیام به کانال وب‌سوکت
            channel_layer = get_channel_layer()
            room_group_name = f'chat_{message.room.id}'

            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'type': 'message_read',
                        'message_id': str(message.id),
                        'read_at': message.read_at.isoformat()
                    }
                }
            )

            return True

        return False

    @staticmethod
    def assign_agent_to_room(room, agent):
        """
        اختصاص پشتیبان به اتاق گفتگو
        """
        if room.agent:
            return False

        room.agent = agent
        room.save(update_fields=['agent'])

        # ایجاد پیام سیستمی
        ChatService.create_system_message(
            room=room,
            content=f"پشتیبان {agent.get_full_name() or agent.username} به گفتگو پیوست."
        )

        return True


class NotificationService:
    @staticmethod
    def create_notification(user, title, message, notification_type='general', data=None):
        """
        ایجاد اعلان جدید
        """
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            data=data or {}
        )

        # ارسال اعلان به کانال وب‌سوکت
        channel_layer = get_channel_layer()
        user_group_name = f'notifications_{user.id}'

        async_to_sync(channel_layer.group_send)(
            user_group_name,
            {
                'type': 'notification_message',
                'message': {
                    'type': 'notification',
                    'notification': {
                        'id': str(notification.id),
                        'title': notification.title,
                        'message': notification.message,
                        'type': notification.notification_type,
                        'data': notification.data,
                        'created_at': notification.created_at.isoformat()
                    }
                }
            }
        )

        return notification

    @staticmethod
    def mark_notification_as_read(notification):
        """
        علامت‌گذاری اعلان به عنوان خوانده شده
        """
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=['is_read'])

            # ارسال پیام به کانال وب‌سوکت
            channel_layer = get_channel_layer()
            user_group_name = f'notifications_{notification.user.id}'

            async_to_sync(channel_layer.group_send)(
                user_group_name,
                {
                    'type': 'notification_message',
                    'message': {
                        'type': 'notification_read',
                        'notification_id': str(notification.id)
                    }
                }
            )

            return True

        return False

    @staticmethod
    def mark_all_notifications_as_read(user):
        """
        علامت‌گذاری تمام اعلان‌های کاربر به عنوان خوانده شده
        """
        count = Notification.objects.filter(user=user, is_read=False).update(is_read=True)

        if count > 0:
            # ارسال پیام به کانال وب‌سوکت
            channel_layer = get_channel_layer()
            user_group_name = f'notifications_{user.id}'

            async_to_sync(channel_layer.group_send)(
                user_group_name,
                {
                    'type': 'notification_message',
                    'message': {
                        'type': 'all_notifications_read'
                    }
                }
            )

        return count