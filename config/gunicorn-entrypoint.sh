#!/bin/bash
set -e

echo "=== Gunicorn Production Server Entrypoint ==="

# تنظیم دایرکتوری‌های مورد نیاز
mkdir -p /app/static /app/staticfiles /app/media /app/logs

# تنظیم محیط تولید
export DJANGO_ENV=production

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