# config/migration_utils.py
import os
import sys
import django
from django.db import connection
from django.core.management import call_command


def setup_django():
    """تنظیم محیط جنگو"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zima.settings')
    django.setup()


def clean_app_migrations(app_name):
    """پاکسازی مایگریشن‌های یک اپلیکیشن خاص"""
    setup_django()

    print(f"Cleaning migrations for {app_name}...")

    # حذف رکوردهای مایگریشن از دیتابیس
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM django_migrations WHERE app = %s", [app_name])

    # حذف جداول مرتبط
    with connection.cursor() as cursor:
        cursor.execute("""
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT table_name FROM information_schema.tables WHERE table_name LIKE %s AND table_schema='public')
            LOOP
                EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.table_name) || ' CASCADE';
                RAISE NOTICE 'Dropped table: %%', r.table_name;
            END LOOP;
        END
        $$;
        """, [f"{app_name}_%"])

    # حذف نوع‌های مرتبط
    with connection.cursor() as cursor:
        cursor.execute("""
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT typname FROM pg_type WHERE typname LIKE %s)
            LOOP
                EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
                RAISE NOTICE 'Dropped type: %%', r.typname;
            END LOOP;
        END
        $$;
        """, [f"{app_name}_%"])

    print(f"Successfully cleaned migrations for {app_name}")


def fake_migrations(app_name=None):
    """اجرای fake migrations برای یک اپلیکیشن یا همه اپلیکیشن‌ها"""
    setup_django()

    if app_name:
        print(f"Fake migrating {app_name}...")
        call_command('migrate', app_name, '--fake')
    else:
        print("Fake migrating all apps...")
        call_command('migrate', '--fake')

    print("Fake migrations completed")


def check_migrations():
    """بررسی وضعیت مایگریشن‌ها"""
    setup_django()
    call_command('showmigrations')


def safe_migrate(app_name=None):
    """اجرای مایگریشن با استراتژی امن"""
    setup_django()

    if app_name:
        print(f"Safely migrating {app_name}...")
        try:
            # اول سعی می‌کنیم با fake-initial
            call_command('migrate', app_name, '--fake-initial')
        except Exception as e:
            print(f"Error with fake-initial: {e}")
            print("Trying with normal migrate...")
            call_command('migrate', app_name)
    else:
        print("Safely migrating all apps...")
        try:
            # اول سعی می‌کنیم با fake-initial
            call_command('migrate', '--fake-initial')
        except Exception as e:
            print(f"Error with fake-initial: {e}")
            print("Trying with normal migrate...")
            call_command('migrate')

    print("Safe migration completed")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migration_utils.py [clean|fake|check|safe] [app_name]")
        sys.exit(1)

    action = sys.argv[1]
    app_name = sys.argv[2] if len(sys.argv) > 2 else None

    if action == 'clean' and app_name:
        clean_app_migrations(app_name)
    elif action == 'fake':
        fake_migrations(app_name)
    elif action == 'check':
        check_migrations()
    elif action == 'safe':
        safe_migrate(app_name)
    else:
        print(f"Unknown action: {action}")
        print("Available actions: clean, fake, check, safe")
        sys.exit(1)