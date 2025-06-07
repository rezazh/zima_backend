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

# بررسی وجود جدول django_migrations
echo "Checking database migration status..."
MIGRATIONS_TABLE_EXISTS=$(PGPASSWORD=$DB_PASSWORD psql -h postgres -U $DB_USER -d $DB_NAME -t -c "
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_name = 'django_migrations'
    );
" | grep -q t && echo "true" || echo "false")

# استراتژی امن برای مایگریشن‌ها
if [ "$MIGRATIONS_TABLE_EXISTS" = "true" ]; then
    echo "Database initialized, using --fake-initial for migrations..."
    python manage.py migrate --fake-initial
else
    echo "New database detected, running initial migrations..."
    python manage.py migrate
fi

# جمع‌آوری فایل‌های استاتیک
echo "Collecting static files..."
python manage.py collectstatic --no-input

# اجرای سرور توسعه Django
echo "Starting Django development server..."
exec python manage.py runserver 0.0.0.0:8000