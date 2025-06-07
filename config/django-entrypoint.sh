#!/bin/bash
set -e

echo "=== Django Development Server Entrypoint ==="

mkdir -p /app/static /app/staticfiles /app/media /app/logs
export DJANGO_ENV=development
export PYTHONPATH=/app
cd /app

echo "Waiting for database..."
while ! nc -z postgres 5432; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done
echo "PostgreSQL is ready!"

echo "Checking database for potential issues..."
if [ -f "/app/config/db_cleanup.sql" ]; then
  PGPASSWORD=$DB_PASSWORD psql -h postgres -U $DB_USER -d $DB_NAME -f /app/config/db_cleanup.sql || echo "Cleanup script execution failed, continuing..."
fi

echo "Running migrations with safe strategy..."
python /app/config/migration_utils.py safe || (
  echo "Safe migration failed, trying alternative approach..." &&
  python manage.py migrate --fake-initial || python manage.py migrate
)

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Starting Django development server..."
exec python manage.py runserver 0.0.0.0:8000