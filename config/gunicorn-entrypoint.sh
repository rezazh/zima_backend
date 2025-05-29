#!/bin/bash
set -e

echo "=== Gunicorn Production Server Entrypoint ==="

# تنظیم دایرکتوری لاگ‌ها
mkdir -p /app/logs

# تغییر تنظیمات جنگو
echo "Modifying Django settings..."
SETTINGS_FILE="/app/zima/settings.py"

if [ -f "$SETTINGS_FILE" ]; then
    echo "Found settings file: $SETTINGS_FILE"

    # بررسی اینکه آیا تنظیمات قبلاً تغییر داده شده‌اند
    if grep -q "Django settings overridden for Docker deployment" "$SETTINGS_FILE"; then
        echo "Settings already modified, skipping..."
    else
        echo "# Django settings overridden for Docker deployment" >> "$SETTINGS_FILE"
        # تنظیمات اضافی را اینجا اضافه کنید
    fi
else
    echo "Settings file not found!"
    exit 1
fi

# انتظار برای دیتابیس
echo "Waiting for database..."
until nc -z -v -w30 postgres 5432
do
  echo "Waiting for postgres database connection..."
  sleep 2
done
echo "PostgreSQL is ready!"

# اجرای مهاجرت‌ها
echo "Running migrations..."
python manage.py migrate

# جمع‌آوری فایل‌های استاتیک
echo "Collecting static files..."
python manage.py collectstatic --noinput

# شروع سرور گونیکورن
echo "Starting Gunicorn server..."
exec gunicorn zima.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --threads 2 \
    --worker-class gthread \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --forwarded-allow-ips='*'