from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import UserStatus

# ⏱ مدت زمان بی‌فعال بودن تا آفلاین کردن (به دقیقه)
INACTIVITY_TIMEOUT_MINUTES = 5


@shared_task
def cleanup_stale_online_statuses():
    """
    این تسک هر دقیقه توسط Celery Beat اجرا می‌شود و کاربران بی‌فعال را آفلاین می‌کند.
    شرط:
      - کاربر status='online' باشد
      - آخرین فعالیت واقعی (last_seen) قدیمی‌تر از INACTIVITY_TIMEOUT_MINUTES باشد
    """
    threshold = timezone.now() - timedelta(minutes=INACTIVITY_TIMEOUT_MINUTES)

    # پیدا کردن کاربران بی‌فعال
    stale_statuses = UserStatus.objects.filter(
        status='online',
        last_seen__lt=threshold
    )

    count = stale_statuses.count()

    if count > 0:
        stale_statuses.update(status='offline')
        return f"Marked {count} stale online users as offline"
    else:
        return "No stale online users found"


@shared_task
def force_offline_disconnected_users():
    """
    این تسک برای مواقعی است که کاربر ارتباط وب‌سوکت را قطع کرده اما
    به هر دلیلی وضعیت‌اش در دیتابیس آنلاین باقی مانده
    (بر اساس heartbeat یا داده‌های اضافی می‌توان تغییر داد)
    """
    heartbeat_threshold = timezone.now() - timedelta(seconds=90)  # 1.5 دقیقه بدون پینگ
    stale_statuses = UserStatus.objects.filter(
        status='online',
        last_heartbeat__lt=heartbeat_threshold
    )

    count = stale_statuses.count()

    if count > 0:
        stale_statuses.update(status='offline')
        return f"Forced {count} disconnected users to offline"
    else:
        return "No disconnected users found"