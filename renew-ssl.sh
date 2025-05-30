#!/bin/bash
# اسکریپت دریافت و تمدید گواهی SSL

# توقف کانتینرها برای آزاد کردن پورت 80
echo "Stopping containers..."
docker-compose down

# نصب certbot اگر نصب نشده است
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    apt-get update
    apt-get install -y certbot
fi

# دریافت یا تمدید گواهی
echo "Obtaining SSL certificate..."
certbot certonly --standalone -d zimabestshop.ir -d www.zimabestshop.ir --non-interactive --agree-tos --email alieroyaei84562@gmail.com

# ایجاد پوشه ssl اگر وجود ندارد
mkdir -p ssl

# کپی فایل‌های گواهی به پوشه پروژه
echo "Copying SSL certificates..."
cp /etc/letsencrypt/live/zimabestshop.ir/fullchain.pem ssl/
cp /etc/letsencrypt/live/zimabestshop.ir/privkey.pem ssl/
cp /etc/letsencrypt/live/zimabestshop.ir/chain.pem ssl/
cp /etc/letsencrypt/live/zimabestshop.ir/cert.pem ssl/

# تنظیم دسترسی‌ها
chmod 644 ssl/*.pem

# راه‌اندازی مجدد کانتینرها
echo "Starting containers..."
docker-compose up -d

echo "SSL certificate has been renewed successfully!"