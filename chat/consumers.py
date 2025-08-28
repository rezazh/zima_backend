import json
import logging
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import ChatRoom, ChatMessage, UserStatus, Notification

User = get_user_model()
logger = logging.getLogger(__name__)
INACTIVITY_TIMEOUT = 300  # 5 دقیقه


# ─────────────── ChatConsumer ───────────────
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']

        if not self.user.is_authenticated or not await self.can_access_room():
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type', '')

            if message_type == 'chat_message':
                content = data.get('message', '')
                file_id = data.get('file_id')
                message = await self.save_message(content, file_id)
                # ارسال پیام به اتاق برای نمایش لحظه‌ای
                await self.channel_layer.group_send(
                    self.room_group_name, {
                        'type': 'chat_message',
                        'message': self.serialize_message(message)
                    }
                )
                # ✅ اصلاح: چک کردن وجود receiver قبل از ارسال اعلان
                receiver_id = await self.get_receiver_id(self.room_id)
                if receiver_id:  # فقط اگر گیرنده وجود داشت
                    await self.channel_layer.group_send(
                        f"notifications_{receiver_id}",
                        {
                            'type': 'chat_unread_update',
                            'room_id': str(self.room_id),
                            'count': await self.get_room_unread_count(receiver_id, self.room_id)
                        }
                    )

            elif message_type == 'mark_read':
                message_id = data.get('message_id')
                success, read_at = await self.mark_message_read(message_id)
                if success:
                    # اطلاع برای همه اعضای روم
                    await self.channel_layer.group_send(
                        self.room_group_name, {
                            'type': 'message_read',
                            'message_id': message_id,
                            'user_id': str(self.user.id),
                            'read_at': read_at.isoformat()
                        }
                    )
                    # بروزرسانی unread روم برای فرستنده
                    sender_id = await self.get_message_sender_id(message_id)
                    if sender_id:
                        await self.channel_layer.group_send(
                            f"notifications_{sender_id}",
                            {
                                'type': 'message_read',
                                'room_id': str(self.room_id),
                                'message_id': message_id,
                                'user_id': str(self.user.id),
                                'read_at': read_at.isoformat()
                            }
                        )

            elif message_type == 'close_room':
                room, error = await self.close_room_in_db()
                if error:
                    await self.send(text_data=json.dumps({'type': 'error', 'message': error}))
                else:
                    # به همه کاربران در روم اطلاع بده که وضعیت تغییر کرده
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'room_status_update',
                            'status': 'closed',
                            'message': f"گفتگو توسط {self.user.username} بسته شد.",
                            'closed_by_staff': self.user.is_staff  # ✅ اضافه شده
                        }
                    )

            # ✅ اضافه شده: پردازش بازگشایی گفتگو
            elif message_type == 'reopen_room':
                room, error = await self.reopen_room_in_db()
                if error:
                    await self.send(text_data=json.dumps({'type': 'error', 'message': error}))
                else:
                    # به همه کاربران در روم اطلاع بده که وضعیت تغییر کرده
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'room_status_update',
                            'status': 'open',
                            'message': f"گفتگو توسط {self.user.username} بازگشایی شد.",
                            'closed_by_staff': False  # ✅ اضافه شده
                        }
                    )

            # ✅ اضافه شده: پردازش تایپینگ
            elif message_type == 'typing':
                is_typing = data.get('is_typing', False)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_typing',
                        'user_id': str(self.user.id),
                        'username': self.user.username,
                        'is_typing': is_typing
                    }
                )

        except Exception as e:
            logger.exception(e)
            await self.send(text_data=json.dumps({'type': 'error', 'message': str(e)}))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    async def message_read(self, event):
        await self.send(text_data=json.dumps({'type': 'message_read', **event}))

    # ✅ اضافه شده: هندلر تایپینگ
    async def user_typing(self, event):
        await self.send(text_data=json.dumps({'type': 'user_typing', **event}))

    @database_sync_to_async
    def can_access_room(self):
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            return self.user.is_staff or room.user == self.user or room.agent == self.user
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content, file_id=None):
        from .models import TemporaryFile  # Import محلی برای جلوگیری از مشکل

        room = ChatRoom.objects.get(id=self.room_id)
        message = ChatMessage.objects.create(
            room=room,
            sender=self.user,
            content=content,
            message_type='text'
        )

        # ✅ اصلاح: پردازش فایل اگر وجود داشته باشد
        if file_id:
            try:
                temp_file = TemporaryFile.objects.get(id=file_id, user=self.user)
                message.file = temp_file.file
                message.save()
                temp_file.delete()  # حذف فایل موقت
            except TemporaryFile.DoesNotExist:
                pass

        return message

    @database_sync_to_async
    def get_receiver_id(self, room_id):
        try:
            room = ChatRoom.objects.select_related('agent', 'user').get(id=room_id)
            # ✅ اصلاح: چک کردن وجود agent قبل از دسترسی
            if room.agent and self.user != room.agent:
                return str(room.agent.id)
            elif room.user and self.user != room.user:
                return str(room.user.id)
            else:
                return None  # اگر هیچ گیرنده‌ای وجود نداشت
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def mark_message_read(self, message_id):
        try:
            msg = ChatMessage.objects.get(id=message_id)
            if msg.sender != self.user and not msg.is_read:
                msg.is_read = True
                msg.read_at = timezone.now()
                msg.save(update_fields=['is_read', 'read_at'])
                return True, msg.read_at
            return False, None
        except ChatMessage.DoesNotExist:
            return False, None

    @database_sync_to_async
    def get_message_sender_id(self, message_id):
        try:
            return ChatMessage.objects.get(id=message_id).sender.id
        except ChatMessage.DoesNotExist:
            return None

    @database_sync_to_async
    def get_room_unread_count(self, user_id, room_id):
        return ChatMessage.objects.filter(room_id=room_id, is_read=False).exclude(sender_id=user_id).count()

    @database_sync_to_async
    def close_room_in_db(self):
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            if not (self.user.is_staff or room.user == self.user):
                return None, "Access Denied"

            room.close(self.user)

            # پیام سیستمی برای بستن چت
            closed_by_username = self.user.username
            message_content = f"گفتگو توسط {closed_by_username} بسته شد."
            ChatMessage.objects.create(room=room, content=message_content, message_type='system')

            return room, None
        except ChatRoom.DoesNotExist:
            return None, "Room not found"

    # ✅ اضافه شده: تابع بازگشایی گفتگو
    @database_sync_to_async
    def reopen_room_in_db(self):
        try:
            room = ChatRoom.objects.get(id=self.room_id)

            # چک کردن مجوز بازگشایی
            can_reopen = False
            if self.user.is_staff:
                can_reopen = True
            elif room.user == self.user and (not room.closed_by or not room.closed_by.is_staff):
                can_reopen = True

            if not can_reopen:
                return None, "شما مجوز بازگشایی این گفتگو را ندارید"

            # بازگشایی گفتگو
            room.status = 'open'
            room.closed_by = None
            room.closed_at = None
            room.save(update_fields=['status', 'closed_by', 'closed_at'])

            # پیام سیستمی برای بازگشایی چت
            reopened_by_username = self.user.username
            message_content = f"گفتگو توسط {reopened_by_username} بازگشایی شد."
            ChatMessage.objects.create(room=room, content=message_content, message_type='system')

            return room, None
        except ChatRoom.DoesNotExist:
            return None, "اتاق گفتگو یافت نشد"

    async def room_status_update(self, event):
        """
        Handles room status updates (e.g., closed, reopened).
        """
        await self.send(text_data=json.dumps({
            'type': 'room_status',
            'status': event['status'],
            'message': event.get('message', ''),
            'closed_by_staff': event.get('closed_by_staff', False)  # ✅ اضافه شده
        }))

    def serialize_message(self, msg):
        return {
            'id': str(msg.id),
            'content': msg.content,
            'sender_id': str(msg.sender.id),
            'sender_name': msg.sender.username,
            'message_type': msg.message_type,
            'file_url': msg.file.url if msg.file else None,
            'is_read': msg.is_read,
            'created_at': msg.created_at.isoformat()
        }


# ─────────────── OnlineStatusConsumer ───────────────
class OnlineStatusConsumer(AsyncWebsocketConsumer):
    user_connections = {}

    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.user_id = str(self.user.id)
        self.group_name = "online_status"

        if self.user_id in self.user_connections:
            old_consumer = self.user_connections[self.user_id]
            try:
                await old_consumer.close(code=4000)
            except:
                pass
        self.user_connections[self.user_id] = self

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.update_user_status('online')
        await self.send_all_statuses()

        self.check_inactive = asyncio.create_task(self.check_inactivity_loop())

    async def disconnect(self, close_code):
        if hasattr(self, 'check_inactive'):
            self.check_inactive.cancel()

        await self.set_user_offline()
        if hasattr(self, 'user_id') and self.user_id in self.user_connections:
            del self.user_connections[self.user_id]

        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'heartbeat':
            await self.update_last_heartbeat()
        elif data.get('type') == 'activity':
            await self.update_last_seen()
        elif data.get('type') == 'set_status':
            await self.update_user_status(data.get('status', 'online'))
        elif data.get('type') == 'offline':
            await self.update_user_status('offline')

    async def check_inactivity_loop(self):
        while True:
            await asyncio.sleep(60)
            user_status = await self.get_user_status_from_db()
            if user_status and (timezone.now() - user_status.last_seen).total_seconds() > INACTIVITY_TIMEOUT:
                await self.update_user_status('offline')

    @database_sync_to_async
    def get_user_status_from_db(self):
        try:
            return UserStatus.objects.get(user=self.user)
        except UserStatus.DoesNotExist:
            return None

    @database_sync_to_async
    def update_last_seen(self):
        return UserStatus.objects.update_or_create(user=self.user, defaults={'last_seen': timezone.now()})

    @database_sync_to_async
    def update_last_heartbeat(self):
        return UserStatus.objects.update_or_create(user=self.user, defaults={'last_heartbeat': timezone.now()})

    @database_sync_to_async
    def set_user_offline(self):
        if hasattr(self, 'user'):
            return UserStatus.objects.filter(user=self.user).update(status='offline')

    @database_sync_to_async
    def update_status_in_db(self, status):
        return UserStatus.objects.update_or_create(user=self.user,
                                                   defaults={'status': status, 'last_seen': timezone.now()})

    async def update_user_status(self, status):
        await self.update_status_in_db(status)
        await self.channel_layer.group_send(
            self.group_name,
            {'type': 'online_status_update', 'user_id': self.user_id, 'status': status}
        )

    async def online_status_update(self, event):
        await self.send(text_data=json.dumps(event))

    async def send_all_statuses(self):
        statuses = await self.get_all_statuses()
        await self.send(text_data=json.dumps({'type': 'all_statuses', 'statuses': statuses}))

    @database_sync_to_async
    def get_all_statuses(self):
        statuses = {uid: 'online' for uid in self.user_connections.keys()}
        for user in User.objects.all():
            uid = str(user.id)
            if uid not in statuses:
                statuses[uid] = 'offline'
        return statuses


# ─────────────── NotificationConsumer ───────────────
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = f"notifications_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_unread_count()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def chat_unread_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_unread_update',
            'room_id': event['room_id'],
            'count': event['count']
        }))

    async def message_read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_read',
            'room_id': event.get('room_id'),
            'message_id': event.get('message_id'),
            'user_id': event.get('user_id'),
            'read_at': event.get('read_at')
        }))

    async def notification_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def unread_count_update(self, event):
        await self.send_unread_count()

    @database_sync_to_async
    def get_unread_count(self):
        return Notification.objects.filter(user=self.user, is_read=False).count()

    async def send_unread_count(self):
        count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': count
        }))


class AdminDashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_authenticated and self.user.is_staff:
            self.group_name = 'admin_dashboard'
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def dashboard_update(self, event):
        await self.send(text_data=json.dumps({
            'type': event['event_type'],
            'data': event['data']
        }))