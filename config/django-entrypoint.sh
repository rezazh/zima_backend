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

# بررسی و اصلاح مشکلات احتمالی در دیتابیس
echo "Checking database for potential issues..."
if [ -f "/app/config/db_cleanup.sql" ]; then
  PGPASSWORD=$DB_PASSWORD psql -h postgres -U $DB_USER -d $DB_NAME -f /app/config/db_cleanup.sql || echo "Cleanup script execution failed, continuing..."
fi

# استراتژی امن برای مایگریشن‌ها با استفاده از اسکریپت پایتون
echo "Running migrations with safe strategy..."
python /app/config/migration_utils.py safe || (
  echo "Safe migration failed, trying alternative approach..." &&
  python manage.py migrate --fake-initial || python manage.py migrate
)

# جمع‌آوری فایل‌های استاتیک
echo "Collecting static files..."
python manage.py collectstatic --no-input

# اجرای سرور توسعه Django
echo "Starting Django development server..."
exec python manage.py runserver 0.0.0.0:8000