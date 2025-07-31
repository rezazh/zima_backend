# chat/middleware.py
import json

from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from .models import UserStatus
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async


class OnlineStatusMiddleware(BaseMiddleware):
    """
    میدلور برای مدیریت وضعیت آنلاین/آفلاین کاربران
    """

    def __init__(self, inner):
        super().__init__(inner)
        self.active_connections = {}  # نگهداری اتصال‌های فعال

    async def __call__(self, scope, receive, send):
        # فقط برای اتصال‌های وب‌سوکت
        if scope['type'] != 'websocket':
            return await self.inner(scope, receive, send)

        # دریافت کاربر
        user = scope.get('user', AnonymousUser())
        if not user.is_authenticated:
            return await self.inner(scope, receive, send)

        connection_id = id(scope)
        user_id = str(user.id)

        # ثبت این اتصال
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(connection_id)

        # تعریف یک تابع جدید برای دریافت پیام‌ها
        original_receive = receive

        async def wrapped_receive():
            message = await original_receive()

            # پردازش پیام‌های وب‌سوکت
            if message['type'] == 'websocket.receive' and 'text' in message:
                try:
                    data = json.loads(message['text'])

                    # ذخیره شناسه اتصال در scope
                    if 'connection_id' in data:
                        scope['connection_id'] = data['connection_id']
                except:
                    pass

            return message

        # تعریف یک تابع جدید برای ارسال پیام‌ها
        original_send = send

        async def wrapped_send(message):
            # ارسال پیام
            await original_send(message)

            # اگر اتصال بسته شد، این اتصال را از لیست حذف کنید
            if message['type'] == 'websocket.close':
                if user_id in self.active_connections and connection_id in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(connection_id)
                    if not self.active_connections[user_id]:
                        del self.active_connections[user_id]

        # اجرای میدلور داخلی با توابع جدید
        return await self.inner(scope, wrapped_receive, wrapped_send)

class ConnectionLimitMiddleware(BaseMiddleware):
    """
    میدلور برای محدود کردن تعداد اتصال‌های همزمان برای هر کاربر
    """

    def __init__(self, inner):
        super().__init__(inner)
        self.connections = {}  # نگهداری تعداد اتصال‌های هر کاربر

    async def __call__(self, scope, receive, send):
        # فقط برای اتصال‌های وب‌سوکت
        if scope['type'] != 'websocket':
            return await self.inner(scope, receive, send)

        # دریافت کاربر
        user = scope.get('user', None)
        if not user or not user.is_authenticated:
            return await self.inner(scope, receive, send)

        user_id = str(user.id)

        # افزایش تعداد اتصال‌ها
        if user_id not in self.connections:
            self.connections[user_id] = 0
        self.connections[user_id] += 1

        # اجرای میدلور داخلی
        try:
            return await self.inner(scope, receive, send)
        finally:
            # کاهش تعداد اتصال‌ها هنگام قطع اتصال
            if user_id in self.connections:
                self.connections[user_id] -= 1
                if self.connections[user_id] <= 0:
                    del self.connections[user_id]

class UserStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response


    def __call__(self, request):
        response = self.get_response(request)

        # بروزرسانی وضعیت کاربر فقط برای کاربران احراز هویت شده
        if request.user.is_authenticated:
            user_status, created = UserStatus.objects.get_or_create(user=request.user)

            # بروزرسانی زمان آخرین بازدید و تنظیم وضعیت به آنلاین
            user_status.status = 'online'
            user_status.save(update_fields=['status', 'last_seen'])  # last_seen با auto_now=True خودکار بروز می‌شود

        return response