#!/bin/bash
echo "=== تست نهایی ==="

echo -e "\n1. تست HTTP:"
curl -I http://localhost:80 | head -5

echo -e "\n2. تست HTTPS:"
curl -Ik https://localhost:443 | head -5

echo -e "\n3. بررسی لاگ‌های جدید nginx:"
docker-compose logs --tail=5 nginx

echo -e "\n4. بررسی وضعیت کانتینرها:"
docker-compose ps | grep nginx

echo -e "\n=== پایان تست ==="
