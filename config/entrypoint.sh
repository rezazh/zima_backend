#!/bin/bash
set -e

echo "=== Starting service: ${SERVICE_TYPE:-gunicorn} ==="

mkdir -p /app/static /app/staticfiles /app/media /app/logs
export PYTHONPATH=/app
cd /app

SERVICE_TYPE=${SERVICE_TYPE:-gunicorn}

# انتظار سریع برای دیتابیس
echo "Checking database..."
timeout=60
while ! nc -z postgres 5432 && [ $timeout -gt 0 ]; do
  sleep 2
  timeout=$((timeout-2))
done

if [ $timeout -le 0 ]; then
  echo "⚠️  Database timeout, but continuing..."
else
  echo "✅ Database ready"
fi

# مایگریشن ساده
echo "Running migrations..."
python manage.py migrate --run-syncdb || echo "Migration issues, continuing..."

# جمع‌آوری static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || echo "Static collection failed"

# اجرای سرویس
case $SERVICE_TYPE in
    "django")
        exec python manage.py runserver 0.0.0.0:8000
        ;;
    "daphne")
        exec daphne -b 0.0.0.0 -p 8001 zima.asgi:application
        ;;
    *)
        exec gunicorn zima.wsgi:application \
            --bind 0.0.0.0:8000 \
            --workers 2 \
            --timeout 60 \
            --log-level info \
            --access-logfile - \
            --error-logfile -
        ;;
esac