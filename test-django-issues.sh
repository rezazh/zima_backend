#!/bin/bash

echo "=== تست مشکلات Django ==="

echo "1. تست دسترسی به Django..."
curl -I http://localhost:8001 2>/dev/null | head -3

echo "2. تست CSRF token..."
curl -c cookies.txt -b cookies.txt http://localhost:8001/ 2>/dev/null | grep -i csrf || echo "CSRF token not found"

echo "3. بررسی لاگ‌های جدید..."
docker-compose logs --tail=5 django

echo "4. تست مسیرهای مختلف..."
curl -I http://localhost:8001/admin/ 2>/dev/null | head -1
curl -I http://localhost:8001/api/ 2>/dev/null | head -1

echo "5. بررسی تنظیمات Django..."
docker-compose exec django python -c "
from django.conf import settings
print('DEBUG:', settings.DEBUG)
print('ALLOWED_HOSTS:', settings.ALLOWED_HOSTS[:3])
"

echo "=== تست کامل شد ==="
