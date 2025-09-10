#!/bin/bash
# A robust deployment script for Docker-based Django projects# Supports a --force flag to redeploy without new commits.
set -e

echo "🚀 Starting deployment process at: $(date)"
echo "==================================================="

# 1. Navigate to the project directory
PROJECT_DIR="/var/www/zimabestshop/zima_backend"
cd $PROJECT_DIR

# 2. Get the current state
OLD_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "none")
echo "ℹ️  Current commit on server: $OLD_COMMIT"

# 3. Fetch the latest changes from the main branch
echo "🔄 Fetching latest changes from remote repository..."
git fetch origin main
git reset --hard origin/main
NEW_COMMIT=$(git rev-parse HEAD)
echo "✅ Pulled latest commit: $NEW_COMMIT"

# ===================================================
#           *** بلوک کد اصلاح شده اینجاست ***# ===================================================
# 4. Check for changes OR a --force flag
echo "🔍 Checking for new commits or force flag..."
if [ "$OLD_COMMIT" = "$NEW_COMMIT" ] && [ "$1" != "--force" ]; then
  echo "✅ No new changes and no --force flag. Deployment is not needed. Exiting."
  echo "💡 To redeploy without new commits, run: ./manual-deploy.sh --force"
  exit 0
fi

if [ "$1" = "--force" ]; then
    echo "⚠️  --force flag detected. Forcing redeployment of commit ${NEW_COMMIT:0:7}..."
else
    echo "🔍 Changes detected. New commits:"
    git log --pretty=format:"- %h %s (%an)" $OLD_COMMIT..$NEW_COMMIT
fi
echo "---------------------------------------------------"
# ===================================================#               *** پایان بلوک اصلاح شده ***
# ===================================================

# 5. Create a database backup before making changes
BACKUP_DIR="/var/www/zimabestshop/backups"
mkdir -p $BACKUP_DIR
BACKUP_FILE="$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"
echo "🛡️  Creating database backup: $BACKUP_FILE"
docker-compose exec -T postgres pg_dumpall -U postgres > $BACKUP_FILE || echo "⚠️  Warning: Database backup failed, but continuing deployment."

# 6. Rebuild and restart all services
echo "🏗️  Bringing down old containers and building new images..."
docker-compose down
docker-compose up -d --build
echo "✅ Containers are up and running."

# 7. Wait for the database service to be fully ready
echo "⏳ Waiting for the database to be ready..."
DB_READY=false
for i in {1..15}; do
  if docker-compose exec -T postgres pg_isready -U postgres -q; then
    echo "✅ Database is ready!"
    DB_READY=true
    break
  fi
  echo "   ... still waiting (attempt $i/15)"  sleep 2
done

if [ "$DB_READY" = false ]; then
  echo "❌ Error: Database did not become ready after 30 seconds. Aborting."
  exit 1
fi

# 8. Apply database migrations and collect static files
echo "⚙️  Running Django management commands..."
echo "   - Applying database migrations..."
docker-compose exec -T django python manage.py migrate --noinput
echo "   - Collecting static files..."
docker-compose exec -T django python manage.py collectstatic --noinput
echo "✅ Management commands completed."

# 9. Final status check
echo "📊 Final container status:"
docker-compose ps "---------------------------------------------------"

# 10. Clean up old resources
echo "🧹 Cleaning up dangling Docker images..."
docker image prune -f
echo "🗑️  Deleting database backups older than 7 days..."find $BACKUP_DIR -name "db_backup_*.sql" -type f -mtime +7 -delete 2>/dev/null || true
echo "✅ Cleanup complete."

echo "🎉 Deployment successful at: $(date)"
echo "Summary: Deployed changes from ${OLD_COMMIT:0:7} to ${NEW_COMMIT:0:7}"
echo "==================================================="
