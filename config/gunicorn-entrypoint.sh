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

# بررسی و اصلاح مشکلات احتمالی در دیتابیس
echo "Checking database for potential issues..."
if [ -f "/app/config/db_cleanup.sql" ]; then
  PGPASSWORD=$DB_PASSWORD psql -h postgres -U $DB_USER -d $DB_NAME -f /app/config/db_cleanup.sql || echo "Cleanup script execution failed, continuing..."
fi

# استراتژی امن برای مایگریشن‌ها با استفاده از اسکریپت پایتون
echo "Running migrations with safe strategy..."
python /app/config/migration_utils.py safe || (
  echo "Safe migration failed, trying alternative approach..." &&

  # بررسی وجود جدول django_migrations
  MIGRATIONS_TABLE_EXISTS=$(python -c "
  import os
  import psycopg2
  try:
      conn = psycopg2.connect(
          dbname=os.environ.get('DB_NAME', 'zima'),
          user=os.environ.get('DB_USER', 'postgres'),
          password=os.environ.get('DB_PASSWORD', 'rezazh79'),
          host=os.environ.get('DB_HOST', 'postgres'),
          port=os.environ.get('DB_PORT', '5432')
      )
      cursor = conn.cursor()
      cursor.execute(\"\"\"
          SELECT EXISTS (
              SELECT FROM information_schema.tables
              WHERE table_name = 'django_migrations'
          );
      \"\"\")
      result = cursor.fetchone()[0]
      print('true' if result else 'false')
      conn.close()
  except Exception as e:
      print('false')
  ")

  if [ "$MIGRATIONS_TABLE_EXISTS" = "true" ]; then
      echo "Database initialized, using --fake-initial..."
      python manage.py migrate --fake-initial
  else
      echo "New database detected, running initial migrations..."
      python manage.py migrate
  fi
)

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