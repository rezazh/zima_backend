from channels.auth import AuthMiddlewareStack
from channels.routing import URLRouter
from channels.sessions import SessionMiddlewareStack
from django.urls import re_path
from . import consumers
from .middleware import ConnectionLimitMiddleware, OnlineStatusMiddleware

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_id>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/online-status/$', consumers.OnlineStatusConsumer.as_asgi()),
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/admin/dashboard/$', consumers.AdminDashboardConsumer.as_asgi()),

]




application = OnlineStatusMiddleware(
    AuthMiddlewareStack(
        SessionMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    )
)