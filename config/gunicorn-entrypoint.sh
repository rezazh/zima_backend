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
    echo "Database initialized, checking for chat app migrations..."
    
    # بررسی وجود رکوردهای مایگریشن برای اپلیکیشن chat
    CHAT_MIGRATIONS_EXIST=$(PGPASSWORD=$DB_PASSWORD psql -h postgres -U $DB_USER -d $DB_NAME -t -c "
        SELECT EXISTS (
            SELECT FROM django_migrations 
            WHERE app = 'chat'
        );
    " | grep -q t && echo "true" || echo "false")
    
    if [ "$CHAT_MIGRATIONS_EXIST" = "true" ]; then
        echo "Chat migrations exist, using --fake for chat app..."
        python manage.py migrate chat --fake
        python manage.py migrate --fake-initial
    else
        echo "No chat migrations found, running normal migrations..."
        python manage.py migrate
    fi
else
    echo "New database detected, running initial migrations..."
    python manage.py migrate
fi

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