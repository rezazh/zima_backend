#!/bin/bash

echo "=== راه‌اندازی مجدد با کانتینر Django جداگانه ==="

echo "1. بررسی گواهی SSL..."
if [ ! -f "config/ssl/fullchain.pem" ] || [ ! -f "config/ssl/privkey.pem" ]; then
    echo "ایجاد گواهی SSL..."
    mkdir -p config/ssl
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout config/ssl/privkey.pem \
        -out config/ssl/fullchain.pem \
        -subj "/CN=zimabestshop.ir/O=ZimaBestShop/C=IR" 2>/dev/null
    chmod 644 config/ssl/fullchain.pem
    chmod 600 config/ssl/privkey.pem
    echo "گواهی SSL ایجاد شد"
else
    echo "گواهی SSL موجود است"
fi

echo "2. توقف کانتینرهای فعلی..."
docker-compose down --remove-orphans
docker stop $(docker ps -q --filter "name=zima_") 2>/dev/null || true
docker rm $(docker ps -aq --filter "name=zima_") 2>/dev/null || true

echo "3. پاک‌سازی شبکه..."
docker network prune -f

echo "4. راه‌اندازی کانتینرهای جدید..."
docker-compose up -d

echo "5. انتظار برای راه‌اندازی..."
sleep 15

echo "6. بررسی وضعیت کانتینرها..."
docker-compose ps

echo "7. تست اتصال HTTP..."
curl -I http://localhost:80 2>/dev/null | head -3 || echo "HTTP test failed"

echo "8. تست اتصال HTTPS..."
curl -Ik https://localhost:443 2>/dev/null | head -3 || echo "HTTPS test failed"

echo "9. تست Django مستقیم..."
curl -I http://localhost:8001 2>/dev/null | head -3 || echo "Django direct test failed"

echo "10. تست سایت اصلی..."
curl -I https://zimabestshop.ir 2>/dev/null | head -3 || echo "Main site test failed"

echo "=== راه‌اندازی کامل شد ==="
echo ""
echo "کانتینرهای شما:"
echo "- zima_postgres: پایگاه داده"
echo "- zima_redis: کش"
echo "- zima_gunicorn: Django production (برای nginx)"
echo "- zima_django: Django development (پورت 8001)"
echo "- zima_nginx: وب سرور (پورت 80 و 443)"
echo ""
echo "دسترسی‌ها:"
echo "- سایت اصلی: https://zimabestshop.ir"
echo "- HTTP محلی: http://localhost:80"
echo "- HTTPS محلی: https://localhost:443"
echo "- Django مستقیم: http://localhost:8001"
