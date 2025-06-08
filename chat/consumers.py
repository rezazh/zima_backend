from django.contrib.auth import get_user_model
from .models import ChatRoom, ChatMessage, UserChatStatus, Notification
from django.utils import timezone
from django.db.models import Q

User = get_user_model()
import json
import base64
import uuid
import os
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.files.base import ContentFile
from django.conf import settings


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']

        # اضافه کردن کاربر به گروه چت
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # تنظیم وضعیت کاربر به آنلاین
        await self.set_user_status('online')
        room = await self.get_room()

        # اعلام به همه کاربران در اتاق که این کاربر آنلاین شده
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status_update',
                'user_id': self.user.id,
                'username': self.user.username,
                'status': 'online',
                'is_staff': self.user.is_staff
            }
        )
        other_user = await self.get_other_user(room)
        if other_user:
            other_user_status = await self.get_user_status(other_user)
            await self.send(text_data=json.dumps({
                'type': 'user_status_update',
                'user_id': other_user.id,
                'username': other_user.username,
                'status': other_user_status,
                'is_staff': other_user.is_staff
            }))
        # علامت‌گذاری پیام‌های خوانده نشده به عنوان خوانده شده
        if not self.user.is_staff:
            await self.mark_messages_as_read()

        await self.accept()

    async def disconnect(self, close_code):
        # حذف کاربر از گروه چت
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # تنظیم وضعیت کاربر به آفلاین
        await self.set_user_status('offline')

        # اعلام به همه کاربران در اتاق که این کاربر آفلاین شده
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status_update',
                'user_id': self.user.id,
                'username': self.user.username,
                'status': 'offline',
                'is_staff': self.user.is_staff
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'chat_message')

        if message_type == 'chat_message':
            message = data.get('message', '')
            file_data = data.get('file', None)

            try:
                if file_data:
                    message_obj = await self.save_message_with_file(message, file_data)
                else:
                    message_obj = await self.save_message(message)

                # بررسی نوع message_obj و استخراج اطلاعات مورد نیاز
                if isinstance(message_obj, dict):
                    message_id = message_obj.get('message_id') or message_obj.get('id')
                    timestamp = message_obj.get('timestamp')
                    message_type = message_obj.get('message_type', 'text')
                    file_url = message_obj.get('file_url')
                    file_name = message_obj.get('file_name')
                    file_type = message_obj.get('file_type')
                else:
                    message_id = str(message_obj.id)
                    timestamp = message_obj.created_at.isoformat()
                    message_type = message_obj.message_type
                    file_url = message_obj.file.url if hasattr(message_obj, 'file') and message_obj.file else None
                    file_name = message_obj.file_name if hasattr(message_obj, 'file_name') else None
                    file_type = message_obj.file_type if hasattr(message_obj, 'file_type') else None

                # ارسال پیام به گروه چت
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'username': self.user.username,
                        'user_id': self.user.id,
                        'message_id': message_id,
                        'timestamp': timestamp,
                        'message_type': message_type,
                        'file_url': file_url,
                        'file_name': file_name,
                        'file_type': file_type,
                        'is_staff': self.user.is_staff,
                    }
                )

                # ارسال اعلان به گیرنده
                receiver = await self.get_receiver()
                if receiver:
                    notification_group_name = f'notifications_{receiver.id}'

                    # ارسال اعلان برای بروزرسانی تعداد پیام‌های خوانده نشده
                    unread_count = await self.get_user_unread_count(receiver)
                    await self.channel_layer.group_send(
                        notification_group_name,
                        {
                            'type': 'unread_count_update',
                            'count': unread_count
                        }
                    )

                    # برای کاربران عادی، اعلان پاپ‌آپ هم ارسال کن
                    if not self.user.is_staff:  # اگر فرستنده ادمین نیست (یعنی کاربر عادی است)
                        if receiver.is_staff:  # و گیرنده ادمین است
                            await self.channel_layer.group_send(
                                notification_group_name,
                                {
                                    'type': 'chat_notification',
                                    'message': message[:50] + ('...' if len(message) > 50 else ''),
                                    'sender': self.user.username,
                                    'room_id': str(self.room_id),
                                    'is_admin': False
                                }
                            )
                    elif not receiver.is_staff:  # اگر فرستنده ادمین است و گیرنده کاربر عادی
                        await self.channel_layer.group_send(
                            notification_group_name,
                            {
                                'type': 'chat_notification',
                                'message': message[:50] + ('...' if len(message) > 50 else ''),
                                'sender': 'پشتیبانی',
                                'room_id': str(self.room_id),
                                'is_admin': True
                            }
                        )
            except Exception as e:
                print(f"Error processing message: {e}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f"خطا در پردازش پیام: {str(e)}"
                }))

        elif message_type == 'typing':
            is_typing = data.get('is_typing', False)
            # ارسال وضعیت تایپ کردن به گروه چت
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_status',
                    'username': self.user.username,
                    'user_id': self.user.id,
                    'is_typing': is_typing,
                    'is_staff': self.user.is_staff
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'message_id': event['message_id'],
            'username': event['username'],
            'user_id': event['user_id'],
            'message_type': event.get('message_type', 'text'),
            'file_url': event.get('file_url', None),
            'file_name': event.get('file_name', None),
            'file_type': event.get('file_type', None),
            'timestamp': event.get('timestamp', None),
            'is_staff': event.get('is_staff', False)
        }))

    async def typing_status(self, event):
        # تغییر نام متد از typing به typing_status برای روشن‌تر بودن
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'username': event['username'],
            'user_id': event['user_id'],
            'is_typing': event['is_typing'],
            'is_staff': event.get('is_staff', False)
        }))

    async def user_status_update(self, event):
        """ارسال بروزرسانی وضعیت کاربر به کلاینت"""
        await self.send(text_data=json.dumps({
            'type': 'user_status_update',
            'user_id': event.get('user_id'),
            'username': event.get('username'),
            'status': event.get('status'),
            'is_staff': event.get('is_staff', False)
        }))

    async def message_read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_read',
            'message_id': event['message_id'],
            'read_by_user_id': event['read_by_user_id']
        }))

    async def chat_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_deleted',
            'deleted_by_user_id': event.get('deleted_by_user_id', None)
        }))

    async def chat_status_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_status_update',
            'is_closed': event['is_closed'],
            'updated_by_user_id': event.get('updated_by_user_id', None)
        }))

    @database_sync_to_async
    def save_message(self, message):
        room = ChatRoom.objects.get(id=self.room_id)
        chat_message = ChatMessage.objects.create(
            room=room,
            sender=self.user,
            content=message,
            message_type='text'
        )
        return chat_message

    @database_sync_to_async
    def get_room(self):
        """دریافت اطلاعات اتاق"""
        try:
            return ChatRoom.objects.get(id=self.room_id)
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def get_other_user(self, room):
        """دریافت کاربر طرف مقابل در چت"""
        if not room:
            return None

        if self.user == room.user:
            return room.admin
        else:
            return room.user

    @database_sync_to_async
    def get_user_status(self, user):
        """دریافت وضعیت واقعی کاربر"""
        if not user:
            return 'offline'

        try:
            status_obj = UserChatStatus.objects.get(user=user)

            # بررسی زمان آخرین فعالیت
            from datetime import timedelta
            threshold = timezone.now() - timedelta(minutes=2)

            if status_obj.last_activity and status_obj.last_activity > threshold:
                return status_obj.status
            else:
                return 'offline'
        except UserChatStatus.DoesNotExist:
            return 'offline'

    @database_sync_to_async
    def set_user_status(self, status):
        """تنظیم وضعیت آنلاین/آفلاین کاربر با به‌روزرسانی زمان فعالیت"""
        try:
            user_status, created = UserChatStatus.objects.get_or_create(
                user=self.user,
                defaults={'status': status}
            )
            user_status.status = status
            user_status.last_activity = timezone.now()
            user_status.save()
        except Exception as e:
            print(f"Error setting user status: {e}")

    @database_sync_to_async
    def get_receiver(self):
        """دریافت کاربر گیرنده پیام"""
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            if self.user == room.user:
                return room.admin
            else:
                return room.user
        except Exception as e:
            print(f"Error in get_receiver: {e}")
            return None

    @database_sync_to_async
    def get_user_unread_count(self, user):
        """محاسبه تعداد پیام‌های خوانده نشده برای یک کاربر خاص"""
        try:
            if user.is_staff:
                return ChatMessage.objects.filter(
                    room__admin=user,
                    is_read=False,
                    sender__is_staff=False
                ).count()
            else:
                return ChatMessage.objects.filter(
                    room__user=user,
                    is_read=False,
                    sender__is_staff=True
                ).count()
        except Exception as e:
            print(f"Error in get_user_unread_count: {e}")
            return 0

    @database_sync_to_async
    def mark_messages_as_read(self):
        """علامت‌گذاری تمام پیام‌های خوانده نشده در این اتاق به عنوان خوانده شده"""
        try:
            room = ChatRoom.objects.get(id=self.room_id)

            # اگر کاربر عادی است، پیام‌های ادمین را خوانده شده علامت‌گذاری کن
            if not self.user.is_staff:
                unread_messages = ChatMessage.objects.filter(
                    room=room,
                    is_read=False,
                    sender__is_staff=True
                )
            else:
                # اگر ادمین است، پیام‌های کاربر را خوانده شده علامت‌گذاری کن
                unread_messages = ChatMessage.objects.filter(
                    room=room,
                    is_read=False,
                    sender__is_staff=False
                )

            for message in unread_messages:
                message.is_read = True
                message.read_at = timezone.now()
                message.save()

                # ارسال رویداد خوانده شدن پیام
                print(f"Sent message_read event for message {message.id}")

            return len(unread_messages)
        except Exception as e:
            print(f"Error marking messages as read: {e}")
            return 0

    @database_sync_to_async
    def save_message_with_file(self, message, file_data):
        room = ChatRoom.objects.get(id=self.room_id)

        file_info = file_data.get('info', {})
        file_name = file_info.get('name', 'unnamed_file')
        file_type = file_info.get('type', 'application/octet-stream')

        max_size = 10 * 1024 * 1024  # 10MB

        file_content_str = file_data.get('content', '')
        if ',' in file_content_str:
            file_content_str = file_content_str.split(',', 1)[1]

        file_content = base64.b64decode(file_content_str)
        file_size = len(file_content)

        if file_size > max_size:
            raise ValueError(f"سایز فایل بیش از حد مجاز است (حداکثر {max_size / (1024 * 1024):.1f} مگابایت)")

        file_ext = os.path.splitext(file_name)[1]
        if not file_ext and '/' in file_type:
            mime_type = file_type.split('/')[1]
            if mime_type == 'jpeg':
                file_ext = '.jpg'
            elif mime_type in ['png', 'gif', 'bmp', 'webp']:
                file_ext = f'.{mime_type}'
            else:
                file_ext = ''

        unique_filename = f"{uuid.uuid4()}{file_ext}"

        chat_message = ChatMessage(
            room=room,
            sender=self.user,
            content=message,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size
        )

        chat_message.file.save(unique_filename, ContentFile(file_content), save=False)

        if file_type.startswith('image/'):
            chat_message.message_type = 'image'
        else:
            chat_message.message_type = 'file'

        chat_message.save()

        if settings.DEBUG:
            file_url = f"{settings.MEDIA_URL}{chat_message.file.name}"
        else:
            file_url = chat_message.file.url

        return chat_message


# اصلاح NotificationConsumer - این بود که مشکل داشت
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        self.notification_group_name = f'notifications_{self.user.id}'

        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )

        await self.accept()

        # ارسال تعداد پیام‌های خوانده نشده در هنگام اتصال
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'notification_group_name'):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'check_unread':
                unread_count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'unread_count',
                    'count': unread_count
                }))
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'message': 'Connection is alive'
                }))
        except json.JSONDecodeError:
            pass

    # اضافه کردن handler مفقود - این بود که مشکل اصلی بود
    async def user_status_update(self, event):
        """Handle user status updates - این handler مفقود بود!"""
        await self.send(text_data=json.dumps({
            'type': 'user_status_update',
            'user_id': event.get('user_id'),
            'username': event.get('username'),
            'status': event.get('status'),
            'is_staff': event.get('is_staff', False)
        }))

    async def chat_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_notification',
            'message': event['message'],
            'sender': event['sender'],
            'room_id': event['room_id'],
            'is_admin': event['is_admin']
        }))

    async def unread_count_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': event['count']
        }))

    # اضافه کردن handler برای notification عمومی
    async def notification_message(self, event):
        """Handle general notification messages"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event.get('message', ''),
            'title': event.get('title', ''),
            'data': event.get('data', {})
        }))

    @database_sync_to_async
    def get_unread_count(self):
        """محاسبه تعداد پیام‌های خوانده نشده برای کاربر فعلی"""
        if not self.user.is_authenticated:
            return 0

        try:
            if self.user.is_staff:
                # برای ادمین‌ها: پیام‌های خوانده نشده از کاربران عادی
                return ChatMessage.objects.filter(
                    room__admin=self.user,
                    is_read=False,
                    sender__is_staff=False
                ).count()
            else:
                # برای کاربران عادی: پیام‌های خوانده نشده از ادمین‌ها
                return ChatMessage.objects.filter(
                    room__user=self.user,
                    is_read=False,
                    sender__is_staff=True
                ).count()
        except Exception as e:
            print(f"Error in get_unread_count: {e}")
            return 0