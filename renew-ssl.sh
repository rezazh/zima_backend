#!/bin/bash
echo "=== تجدید گواهی SSL ==="

# تجدید گواهی
docker-compose run --rm certbot renew

# کپی گواهی‌های جدید
if [ -f "./certbot/conf/live/zimabestshop.ir/fullchain.pem" ]; then
    cp ./certbot/conf/live/zimabestshop.ir/fullchain.pem ./config/ssl/
    cp ./certbot/conf/live/zimabestshop.ir/privkey.pem ./config/ssl/
    echo "گواهی SSL تجدید شد"
    
    # راه‌اندازی مجدد nginx
    docker-compose restart nginx
else
    echo "تجدید گواهی انجام نشد"
fi
