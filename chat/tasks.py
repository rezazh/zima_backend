# tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import UserStatus


@shared_task
def cleanup_stale_online_statuses():
    # کاربرانی که بیش از 5 دقیقه فعالیت نداشته‌اند را آفلاین کنید
    threshold = timezone.now() - timedelta(minutes=5)
    stale_statuses = UserStatus.objects.filter(
        status='online',
        last_seen__lt=threshold
    )

    count = stale_statuses.count()
    stale_statuses.update(status='offline')

    return f"Marked {count} stale online statuses as offline"