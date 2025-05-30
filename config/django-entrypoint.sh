#!/bin/bash
set -e

echo "=== Django Development Server Entrypoint ==="

# تنظیم دایرکتوری‌های مورد نیاز
mkdir -p /app/static /app/staticfiles /app/media /app/logs

# تنظیم محیط توسعه
export DJANGO_ENV=development

# انتظار برای آماده شدن پایگاه داده
echo "Waiting for database..."
while ! nc -z postgres 5432; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done
echo "PostgreSQL is ready!"

# اجرای migrations
echo "Running migrations..."
python manage.py migrate --no-input

# جمع‌آوری فایل‌های استاتیک
echo "Collecting static files..."
python manage.py collectstatic --no-input

# اجرای سرور توسعه Django
echo "Starting Django development server..."
exec python manage.py runserver 0.0.0.0:8000