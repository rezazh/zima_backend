from django.utils import timezone
from .models import UserChatStatus


class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # بروزرسانی آخرین زمان فعالیت کاربر
        if request.user.is_authenticated:
            try:
                status, created = UserChatStatus.objects.get_or_create(user=request.user)
                status.last_seen = timezone.now()
                if request.path != '/chat/set-offline/':  # اگر درخواست برای آفلاین شدن نیست
                    status.status = 'online'
                status.save(update_fields=['last_seen', 'status'])
            except Exception as e:
                pass

        return response