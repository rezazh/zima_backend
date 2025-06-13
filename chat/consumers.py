import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import ChatRoom, ChatMessage, UserStatus, Notification
from django.contrib.auth import get_user_model
import logging

from .services import UserStatusService

User = get_user_model()
logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']

        # بررسی اینکه آیا کاربر مجاز به دسترسی به این اتاق است
        if not self.user.is_authenticated or not await self.can_access_room():
            await self.close()
            return

        # پیوستن به گروه اتاق
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # اعلام آنلاین شدن کاربر به سایر کاربران اتاق
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': str(self.user.id),
                'status': 'online',
                'username': self.user.username
            }
        )

    async def disconnect(self, close_code):
        # خروج از گروه اتاق
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type', '')

            if message_type == 'chat_message':
                # دریافت پیام چت
                content = data['message']
                file_id = data.get('file_id')

                # ذخیره پیام در دیتابیس
                try:
                    message = await self.save_message(content, file_id)

                    # ارسال پیام به گروه اتاق
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': {
                                'id': str(message.id),
                                'content': message.content,
                                'sender_id': str(message.sender.id),
                                'sender_name': message.sender.username,
                                'message_type': message.message_type,
                                'file': message.file.url if message.file else None,
                                'is_read': message.is_read,
                                'created_at': message.created_at.isoformat()
                            }
                        }
                    )
                except Exception as e:
                    # ارسال خطا به کلاینت
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': str(e)
                    }))

            elif message_type == 'mark_read':
                # علامت‌گذاری پیام به عنوان خوانده شده
                message_id = data['message_id']
                success, read_at = await self.mark_message_read(message_id)

                if success and read_at:
                    # اعلام به گروه اتاق که پیام خوانده شده است
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'message_read',
                            'message_id': message_id,
                            'user_id': str(self.user.id),
                            'read_at': read_at.isoformat()
                        }
                    )

            elif message_type == 'typing':
                # اعلام تایپ کردن کاربر
                is_typing = data['is_typing']

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_typing',
                        'user_id': str(self.user.id),
                        'username': self.user.username,
                        'is_typing': is_typing
                    }
                )

            elif message_type == 'close_room':
                # بستن اتاق گفتگو
                success = await self.close_room()

                if success:
                    # اعلام به گروه اتاق که گفتگو بسته شده است
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'room_closed',
                            'user_id': str(self.user.id),
                            'is_admin': self.user.is_staff,
                            'closed_at': timezone.now().isoformat()
                        }
                    )

            elif message_type == 'reopen_room':
                # بازگشایی اتاق گفتگو
                success = await self.reopen_room()

                if success:
                    # اعلام به گروه اتاق که گفتگو بازگشایی شده است
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'room_reopened',
                            'user_id': str(self.user.id),
                            'is_admin': self.user.is_staff,
                            'reopened_at': timezone.now().isoformat()
                        }
                    )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def get_room(self):
        """
        دریافت اتاق گفتگو از پایگاه داده
        """
        room_id = self.room_id
        try:
            return await database_sync_to_async(ChatRoom.objects.get)(id=room_id)
        except ChatRoom.DoesNotExist:
            raise ValueError(f"اتاق گفتگو با شناسه {room_id} یافت نشد.")

    async def create_system_message(self, content):
        room = await self.get_room()
        message = await database_sync_to_async(ChatMessage.objects.create)(
            room=room,
            content=content,
            message_type='system',
            is_read=True
        )
        return message

    async def chat_deleted_by_user(self, event):
        """اطلاع‌رسانی به کاربر در مورد حذف گفتگو توسط کاربر دیگر"""
        # استفاده از نام کاربر به جای deleted_by
        username = event.get('username', 'کاربر')

        await self.send(text_data=json.dumps({
            'type': 'chat_deleted',
            'room_id': event['room_id'],
            'deleted_by_username': username  # استفاده از نام کاربر
        }))

    async def chat_message(self, event):
        """ارسال پیام چت به کلاینت"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    async def message_read(self, event):
        """ارسال وضعیت خوانده شدن پیام به کلاینت"""
        await self.send(text_data=json.dumps({
            'type': 'message_read',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'read_at': event['read_at']
        }))

    async def user_typing(self, event):
        """ارسال وضعیت تایپ کردن کاربر به کلاینت"""
        await self.send(text_data=json.dumps({
            'type': 'user_typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))

    async def user_status(self, event):
        """ارسال وضعیت آنلاین/آفلاین کاربر به کلاینت"""
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user_id': event['user_id'],
            'status': event['status'],
            'username': event['username']
        }))

    async def room_closed(self, event):
        """ارسال وضعیت بسته شدن اتاق به کلاینت"""
        await self.send(text_data=json.dumps({
            'type': 'room_closed',
            'user_id': event['user_id'],
            'is_admin': event['is_admin'],
            'closed_at': event['closed_at']
        }))

    async def room_reopened(self, event):
        """ارسال وضعیت بازگشایی اتاق به کلاینت"""
        await self.send(text_data=json.dumps({
            'type': 'room_reopened',
            'user_id': event['user_id'],
            'is_admin': event['is_admin'],
            'reopened_at': event['reopened_at']
        }))

    @database_sync_to_async
    def can_access_room(self):
        """بررسی دسترسی کاربر به اتاق گفتگو"""
        try:
            room = ChatRoom.objects.get(id=self.room_id)

            # اگر کاربر پشتیبان است
            if self.user.is_staff:
                return not room.is_deleted_by_agent

            # اگر کاربر عادی است
            return room.user == self.user and not room.is_deleted_by_user
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content, file_id=None):
        """ذخیره پیام در دیتابیس"""
        room = ChatRoom.objects.get(id=self.room_id)

        # بررسی وضعیت اتاق
        if room.status != 'open':
            raise ValueError("اتاق گفتگو بسته شده است و امکان ارسال پیام وجود ندارد.")

        # ایجاد پیام جدید
        message = ChatMessage.objects.create(
            room=room,
            sender=self.user,
            content=content,
            message_type='text'
        )

        # اگر فایل وجود دارد، آن را به پیام اضافه می‌کنیم
        if file_id:
            from .models import TemporaryFile
            try:
                temp_file = TemporaryFile.objects.get(id=file_id, user=self.user)
                message.file = temp_file.file
                message.save(update_fields=['file'])
                temp_file.delete()  # حذف فایل موقت
            except TemporaryFile.DoesNotExist:
                pass

        return message

    @database_sync_to_async
    def mark_message_read(self, message_id):
        """علامت‌گذاری پیام به عنوان خوانده شده"""
        try:
            message = ChatMessage.objects.get(id=message_id)

            # فقط پیام‌های دریافتی را می‌توان به عنوان خوانده شده علامت‌گذاری کرد
            if message.sender != self.user and not message.is_read:
                message.is_read = True
                message.read_at = timezone.now()
                message.save(update_fields=['is_read', 'read_at'])
                return True, message.read_at

            return False, None
        except ChatMessage.DoesNotExist:
            return False, None

    async def close_room(self):
        """بستن اتاق گفتگو"""
        try:
            room = await self.get_room()

            # تنظیم وضعیت اتاق به بسته شده
            room.status = 'closed'
            room.closed_at = timezone.now()
            room.closed_by = self.user
            await database_sync_to_async(room.save)()

            # ایجاد پیام سیستمی
            message_text = 'این گفتگو توسط پشتیبانی بسته شده است.' if self.user.is_staff else 'این گفتگو توسط کاربر بسته شده است.'
            await self.create_system_message(message_text)

            # ارسال وضعیت جدید به همه کاربران
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'room_status',
                    'status': 'closed',
                    'closed_by_staff': self.user.is_staff,
                    'closed_by_id': str(self.user.id),
                    'message': message_text
                }
            )

        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'خطا در بستن اتاق گفتگو: {str(e)}'
            }))
            import traceback
            traceback.print_exc()

    async def reopen_room(self):
        """بازگشایی اتاق گفتگو"""
        try:
            room = await self.get_room()

            # تنظیم وضعیت اتاق به باز
            room.status = 'open'
            room.closed_at = None
            room.closed_by = None
            await database_sync_to_async(room.save)()

            # ایجاد پیام سیستمی
            message_text = 'این گفتگو بازگشایی شده است.'
            await self.create_system_message(message_text)

            # ارسال وضعیت جدید به همه کاربران
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'room_status',
                    'status': 'open',
                    'message': message_text
                }
            )

        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'خطا در بازگشایی اتاق گفتگو: {str(e)}'
            }))
            import traceback
            traceback.print_exc()

    async def room_status(self, event):
        """ارسال وضعیت اتاق به کلاینت"""
        try:
            # ایجاد پیام با تمام فیلدهای لازم
            message = {
                'type': 'room_status',
                'status': event['status'],
            }

            # اضافه کردن فیلدهای اختیاری
            for field in ['closed_by_staff', 'closed_by_id', 'message']:
                if field in event:
                    message[field] = event[field]

            # ارسال پیام به کلاینت
            await self.send(text_data=json.dumps(message))

        except Exception as e:
            import traceback
            traceback.print_exc()


# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import UserStatus


class OnlineStatusConsumer(AsyncWebsocketConsumer):
    # نگهداری اتصال‌های کاربران (فقط یک اتصال برای هر کاربر)
    user_connections = {}

    async def connect(self):
        """اتصال به وب‌سوکت"""
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        self.user_id = str(self.user.id)
        self.group_name = "online_status"

        # بررسی و بستن اتصال قبلی
        if self.user_id in self.user_connections:
            old_consumer = self.user_connections[self.user_id]
            try:
                # بستن اتصال قبلی با کد خاص
                await old_consumer.close(code=4000)
                logger.info(f"Closed old connection for user {self.user.username}")
            except Exception as e:
                logger.warning(f"Error closing old connection: {e}")

        # ثبت این اتصال
        self.user_connections[self.user_id] = self

        # پیوستن به گروه
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # پذیرش اتصال
        await self.accept()

        # تنظیم وضعیت به آنلاین
        await self.update_user_status('online')

        # ارسال وضعیت همه کاربران
        await self.send_all_statuses()

        logger.info(f"User {self.user.username} connected to online status websocket")

    async def disconnect(self, close_code):
        """قطع اتصال از وب‌سوکت"""
        if not hasattr(self, 'user') or not self.user.is_authenticated:
            return

        # حذف این اتصال فقط اگر همان اتصال فعلی باشد
        if (hasattr(self, 'user_id') and
                self.user_id in self.user_connections and
                self.user_connections[self.user_id] == self):

            del self.user_connections[self.user_id]

            # تنظیم وضعیت به آفلاین فقط اگر اتصال جدیدی وجود نداشته باشد
            if close_code != 4000:  # 4000 = بسته شده توسط اتصال جدید
                await self.update_user_status('offline')

        # خروج از گروه
        try:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
        except Exception as e:
            logger.warning(f"Error leaving group: {e}")

        logger.info(f"User {self.user.username} disconnected from online status websocket")

    async def receive(self, text_data):
        """دریافت پیام از کلاینت"""
        try:
            data = json.loads(text_data)

            if data.get('type') == 'heartbeat':
                await self.update_last_seen()

            elif data.get('type') == 'set_status':
                status = data.get('status', 'online')
                await self.update_user_status(status)

            elif data.get('type') == 'offline':
                await self.update_user_status('offline')
                logger.info(f"User {self.user.username} set to offline")

        except Exception as e:
            logger.error(f"Error in OnlineStatusConsumer.receive: {e}")

    async def online_status_update(self, event):
        """ارسال به‌روزرسانی وضعیت کاربر به کلاینت"""
        try:
            # بررسی وضعیت اتصال قبل از ارسال
            if (hasattr(self, 'channel_name') and
                    hasattr(self, 'user_id') and
                    self.user_id in self.user_connections and
                    self.user_connections[self.user_id] == self):
                await self.send(text_data=json.dumps({
                    'type': 'status_update',
                    'user_id': event['user_id'],
                    'status': event['status']
                }))
        except Exception as e:
            logger.warning(f"Error sending status update: {e}")

    async def update_user_status(self, status):
        """به‌روزرسانی وضعیت کاربر در دیتابیس و ارسال به همه کاربران"""
        try:
            # به‌روزرسانی در دیتابیس
            await self.update_status_in_db(status)

            # ارسال به همه کاربران
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'online_status_update',
                    'user_id': self.user_id,
                    'status': status
                }
            )

        except Exception as e:
            logger.error(f"Error updating user status: {e}")

    @database_sync_to_async
    def update_status_in_db(self, status):
        """به‌روزرسانی وضعیت کاربر در دیتابیس"""
        try:
            user_status, created = UserStatus.objects.update_or_create(
                user=self.user,
                defaults={
                    'status': status,
                    'last_seen': timezone.now()
                }
            )
            return user_status
        except Exception as e:
            logger.error(f"Error updating status in DB: {e}")
            return None

    @database_sync_to_async
    def update_last_seen(self):
        """به‌روزرسانی زمان آخرین فعالیت کاربر"""
        try:
            user_status, created = UserStatus.objects.update_or_create(
                user=self.user,
                defaults={
                    'last_seen': timezone.now()
                }
            )
            return user_status
        except Exception as e:
            logger.error(f"Error updating last seen: {e}")
            return None

    async def send_all_statuses(self):
        """ارسال وضعیت همه کاربران به کلاینت"""
        try:
            statuses = await self.get_all_statuses()
            await self.send(text_data=json.dumps({
                'type': 'all_statuses',
                'statuses': statuses
            }))
        except Exception as e:
            logger.error(f"Error sending all statuses: {e}")

    @database_sync_to_async
    def get_all_statuses(self):
        """دریافت وضعیت همه کاربران"""
        User = get_user_model()
        statuses = {}

        # دریافت وضعیت کاربران آنلاین از اتصال‌های فعال
        for user_id in self.user_connections.keys():
            statuses[user_id] = 'online'

        # دریافت وضعیت سایر کاربران از دیتابیس
        for user in User.objects.all():
            user_id = str(user.id)
            if user_id not in statuses:
                try:
                    user_status = UserStatus.objects.get(user=user)
                    # اگر کاربر در اتصال‌های فعال نیست، آفلاین است
                    statuses[user_id] = 'offline'
                except UserStatus.DoesNotExist:
                    statuses[user_id] = 'offline'

        return statuses

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        self.notification_group_name = f'notifications_{self.user.id}'

        # پیوستن به گروه اعلان‌ها
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )

        await self.accept()

        # ارسال تعداد اعلان‌های خوانده نشده به کاربر
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))

    async def disconnect(self, close_code):
        if not self.user.is_authenticated:
            return

        # خروج از گروه اعلان‌ها
        await self.channel_layer.group_discard(
            self.notification_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action', '')

            if action == 'mark_read':
                # علامت‌گذاری اعلان به عنوان خوانده شده
                notification_id = data.get('notification_id')
                success = await self.mark_notification_read(notification_id)

                if success:
                    # ارسال تعداد اعلان‌های خوانده نشده به کاربر
                    unread_count = await self.get_unread_count()
                    await self.send(text_data=json.dumps({
                        'type': 'unread_count',
                        'count': unread_count
                    }))

            elif action == 'mark_all_read':
                # علامت‌گذاری تمام اعلان‌ها به عنوان خوانده شده
                success = await self.mark_all_notifications_read()

                if success:
                    # ارسال تعداد اعلان‌های خوانده نشده به کاربر
                    await self.send(text_data=json.dumps({
                        'type': 'unread_count',
                        'count': 0
                    }))

            elif action == 'heartbeat':
                # پاسخ به heartbeat
                await self.send(text_data=json.dumps({
                    'type': 'heartbeat_response',
                    'timestamp': timezone.now().isoformat()
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def notification_message(self, event):
        """ارسال اعلان جدید به کلاینت"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))

        # به‌روزرسانی تعداد اعلان‌های خوانده نشده
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))

    @database_sync_to_async
    def get_unread_count(self):
        """دریافت تعداد اعلان‌های خوانده نشده"""
        if not self.user.is_authenticated:
            return 0

        return Notification.objects.filter(user=self.user, is_read=False).count()

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """علامت‌گذاری اعلان به عنوان خوانده شده"""
        try:
            notification = Notification.objects.get(id=notification_id, user=self.user)
            notification.is_read = True
            notification.save(update_fields=['is_read'])
            return True
        except Notification.DoesNotExist:
            return False

    @database_sync_to_async
    def mark_all_notifications_read(self):
        """علامت‌گذاری تمام اعلان‌ها به عنوان خوانده شده"""
        Notification.objects.filter(user=self.user, is_read=False).update(is_read=True)
        return True
