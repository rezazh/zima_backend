#!/bin/bash

echo "=== تنظیم لاگ‌های Django ==="

echo "1. ایجاد دایرکتوری لاگ..."
mkdir -p logs
chmod 777 logs

echo "2. تست لاگ‌های Django..."
docker-compose exec django python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('django')
logger.info('Test log message')
print('Log test completed')
"

echo "3. بررسی فایل‌های لاگ..."
ls -la logs/

echo "4. نمایش آخرین لاگ‌های Django..."
if [ -f "logs/django.log" ]; then
    tail -10 logs/django.log
else
    echo "فایل لاگ Django یافت نشد"
fi

echo "5. نمایش لاگ‌های کانتینر Django..."
docker-compose logs --tail=10 django

echo "=== تنظیم لاگ‌ها کامل شد ==="
