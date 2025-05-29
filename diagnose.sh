#!/bin/bash
echo "=== تشخیص مشکل پورت 443 ==="

echo -e "\n1. بررسی nginx سیستم:"
systemctl is-active nginx 2>/dev/null || echo "nginx سیستم فعال نیست"

echo -e "\n2. بررسی apache2 سیستم:"
systemctl is-active apache2 2>/dev/null || echo "apache2 سیستم فعال نیست"

echo -e "\n3. بررسی پورت‌های اشغال شده:"
netstat -tlnp | grep -E ':(80|443)'

echo -e "\n4. بررسی پروسه‌های پورت 443:"
lsof -i :443 2>/dev/null || echo "هیچ پروسه‌ای روی پورت 443 یافت نشد"

echo -e "\n5. بررسی وضعیت کانتینرها:"
docker-compose ps

echo -e "\n6. بررسی لاگ‌های nginx:"
docker-compose logs --tail=10 nginx

echo -e "\n7. بررسی فایروال:"
ufw status

echo -e "\n8. تست اتصال داخلی کانتینر:"
docker-compose exec nginx netstat -tlnp 2>/dev/null || echo "نمی‌توان به کانتینر متصل شد"

echo -e "\n=== پایان تشخیص ==="
