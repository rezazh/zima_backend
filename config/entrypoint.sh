#!/bin/bash
set -e

echo "=== Django/Gunicorn/Daphne Entrypoint ==="

# تنظیم دایرکتوری‌های مورد نیاز
mkdir -p /app/static /app/staticfiles /app/media /app/logs

export PYTHONPATH=/app
cd /app

SERVICE_TYPE=${SERVICE_TYPE:-gunicorn}

# انتظار برای دیتابیس
echo "Waiting for database..."
timeout=120   # حداکثر ۲ دقیقه صبر می‌کند
while ! nc -z postgres 5432; do
  echo "Waiting for postgres database connection..."
  sleep 2
  timeout=$((timeout-2))
  if [ $timeout -le 0 ]; then
    echo "Database connection timeout!"
    exit 1
  fi
done
echo "PostgreSQL is ready!"

# اجرای مایگریشن‌ها
echo "Running migrations..."
if python manage.py migrate --fake-initial 2>/dev/null; then
    echo "Migrations completed with --fake-initial"
elif python manage.py migrate 2>/dev/null; then
    echo "Migrations completed normally"
else
    echo "Migration failed, but continuing..."
fi

# جمع‌آوری فایل‌های استاتیک
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Static collection failed, continuing..."

# اجرای سرویس مناسب
case $SERVICE_TYPE in
    "django")
        echo "Starting Django development server..."
        exec python manage.py runserver 0.0.0.0:8000
        ;;
    "daphne")
        echo "Starting Daphne server..."
        exec daphne -b 0.0.0.0 -p 8001 zima.asgi:application
        ;;
    *)
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
        ;;
esac