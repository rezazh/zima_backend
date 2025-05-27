#!/bin/bash

set -e

echo "=== Django Development Server Entrypoint ==="

# ایجاد دایرکتوری‌های مورد نیاز
mkdir -p /app/static /app/staticfiles /app/media /app/logs

# اصلاح تنظیمات Django
echo "Modifying Django settings..."
SETTINGS_FILE=$(find /app -name "settings.py" -path "*/zima/*" | head -1)

if [ -n "$SETTINGS_FILE" ]; then
    echo "Found settings file: $SETTINGS_FILE"

    # بررسی اینکه آیا تنظیمات قبلاً اضافه شده‌اند یا نه
    if ! grep -q "Override settings for Docker deployment" "$SETTINGS_FILE"; then
        # اضافه کردن تنظیمات override
        cat >> "$SETTINGS_FILE" << 'EOF'

# Override settings for Docker deployment
import os

# اجازه دادن به تمام میزبان‌ها
ALLOWED_HOSTS = ['*']

# تنظیم پایگاه داده برای Docker
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'zima'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'rezazh79'),
        'HOST': os.environ.get('DB_HOST', 'postgres'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'disable',
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 600,
    }
}

# غیرفعال کردن تنظیمات HTTPS در محیط توسعه
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

print("Django settings overridden for Docker deployment")
EOF
        echo "Settings file modified successfully"
    else
        echo "Settings already modified, skipping..."
    fi
else
    echo "Settings file not found!"
    exit 1
fi

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