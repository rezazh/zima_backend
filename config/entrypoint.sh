#!/bin/bash
set -e

echo "=== Starting service: ${SERVICE_TYPE:-gunicorn} ==="

# ایجاد دایرکتوری‌ها
mkdir -p /app/static /app/staticfiles /app/media

export PYTHONPATH=/app
cd /app

SERVICE_TYPE=${SERVICE_TYPE:-gunicorn}

# انتظار برای دیتابیس
echo "Checking database connection..."
timeout=60
while ! nc -z postgres 5432 && [ $timeout -gt 0 ]; do
  sleep 2
  timeout=$((timeout-2))
done

if [ $timeout -le 0 ]; then
  echo "⚠️  Database connection timeout, but continuing..."
else
  echo "✅ Database is ready!"
fi

# تنظیم logging برای Docker
export USE_FILE_LOGGING=false

# مایگریشن ساده
echo "Running migrations..."
python manage.py migrate --run-syncdb || echo "Migration failed, continuing..."

# جمع‌آوری static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || echo "Static collection failed, continuing..."

# اجرای سرویس
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
            --workers 2 \
            --timeout 60 \
            --log-level info \
            --access-logfile - \
            --error-logfile - \
            --capture-output
        ;;
esac