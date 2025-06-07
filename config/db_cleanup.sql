-- config/db_cleanup.sql
-- اسکریپت هوشمند برای پاکسازی جداول مشکل‌دار

-- بررسی وجود جداول chat و تصمیم‌گیری برای پاکسازی
DO $$
DECLARE
    chat_tables_count INTEGER;
    chat_migrations_count INTEGER;
    duplicate_types_count INTEGER;
BEGIN
    -- بررسی وجود جدول django_migrations
    PERFORM 1 FROM information_schema.tables WHERE table_name = 'django_migrations';
    IF NOT FOUND THEN
        RAISE NOTICE 'Table django_migrations does not exist. Skipping cleanup.';
        RETURN;
    END IF;

    -- بررسی تعداد جداول chat
    SELECT COUNT(*) INTO chat_tables_count
    FROM information_schema.tables
    WHERE table_name LIKE 'chat_%' AND table_schema='public';

    -- بررسی تعداد رکوردهای مایگریشن chat
    BEGIN
        SELECT COUNT(*) INTO chat_migrations_count
        FROM django_migrations
        WHERE app='chat';
    EXCEPTION WHEN OTHERS THEN
        chat_migrations_count := 0;
    END;

    -- بررسی وجود نوع‌های تکراری
    SELECT COUNT(*) INTO duplicate_types_count
    FROM (
        SELECT typname, typnamespace, COUNT(*) as count
        FROM pg_type
        WHERE typname LIKE 'chat_%'
        GROUP BY typname, typnamespace
        HAVING COUNT(*) > 1
    ) as subquery;

    -- اگر مشکلی وجود دارد، پاکسازی را انجام می‌دهیم
    IF (chat_tables_count > 0 AND chat_migrations_count = 0) OR duplicate_types_count > 0 THEN
        RAISE NOTICE 'Detected inconsistency in chat tables. Cleaning up...';

        -- حذف رکوردهای مایگریشن مربوط به chat
        DELETE FROM django_migrations WHERE app='chat';

        -- حذف نوع‌های موجود در پایگاه داده
        FOR r IN (SELECT typname FROM pg_type WHERE typname LIKE 'chat_%') LOOP
            EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
            RAISE NOTICE 'Dropped type: %', r.typname;
        END LOOP;

        -- حذف جداول چت
        FOR r IN (SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'chat_%' AND table_schema='public') LOOP
            EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.table_name) || ' CASCADE';
            RAISE NOTICE 'Dropped table: %', r.table_name;
        END LOOP;

        RAISE NOTICE 'Cleanup completed successfully.';
    ELSE
        RAISE NOTICE 'No inconsistency detected in chat tables. Skipping cleanup.';
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error during cleanup: %', SQLERRM;
END
$$;