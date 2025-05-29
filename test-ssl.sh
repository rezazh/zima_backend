#!/bin/bash
echo "=== تست کامل سیستم ==="

# بررسی وضعیت کانتینرها
echo -e "\n=== وضعیت کانتینرها ==="
docker-compose ps

# بررسی پورت‌های باز
echo -e "\n=== پورت‌های باز ==="
netstat -tlnp | grep -E ':(80|443|8000)'

# تست HTTP
echo -e "\n=== تست HTTP ==="
curl -I http://localhost:80 2>/dev/null || echo "HTTP failed"

# تست HTTPS
echo -e "\n=== تست HTTPS ==="
curl -Ik https://localhost:443 2>/dev/null || echo "HTTPS failed"

# تست Gunicorn
echo -e "\n=== تست Gunicorn ==="
curl -I http://localhost:8000 2>/dev/null || echo "Gunicorn failed"

# بررسی لاگ‌های nginx
echo -e "\n=== لاگ‌های Nginx ==="
docker-compose logs --tail=10 nginx

echo -e "\n=== پایان تست ==="
