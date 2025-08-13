import os
from celery import Celery

# ست کردن مسیر تنظیمات پیش‌فرض جنگو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zima.settings')

app = Celery('zima')

# خواندن تنظیمات از settings.py (با پیشوند CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# شناسایی تمام tasks.py در اپ‌ها
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')