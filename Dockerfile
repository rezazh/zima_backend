# استفاده از تصویر رسمی پایتون 3.11 با سیستم عامل آلپاین که کم‌حجم و امن است
# آلپاین نسخه سبک لینوکس است که برای کانتینرها بهینه شده است
FROM python:3.11-alpine

# تنظیم متغیرهای محیطی
# PYTHONDONTWRITEBYTECODE: از ایجاد فایل‌های پایکد (__pycache__) جلوگیری می‌کند
# PYTHONUNBUFFERED: از بافر شدن خروجی پایتون جلوگیری می‌کند و لاگ‌ها بلافاصله نمایش داده می‌شوند
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # تنظیم مسیر نصب پکیج‌های پایتون
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    # تنظیم دایرکتوری کاری
    APP_HOME=/app

# ایجاد و تنظیم دایرکتوری کاری
# این دستور یک دایرکتوری به نام /app ایجاد می‌کند و آن را به عنوان دایرکتوری کاری تنظیم می‌کند
WORKDIR $APP_HOME

# نصب پکیج‌های مورد نیاز سیستمی
# این پکیج‌ها برای کامپایل و اجرای برخی پکیج‌های پایتون مانند Psycopg2 (درایور PostgreSQL) مورد نیاز هستند
RUN apk update \
    && apk add --no-cache \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev \
    jpeg-dev \
    zlib-dev \
    libffi-dev \
    gettext \
    # نصب Nginx برای سرو فایل‌های استاتیک
    nginx

# کپی فایل‌های مورد نیاز برای نصب وابستگی‌ها
# ابتدا فقط فایل requirements.txt را کپی می‌کنیم تا از کش Docker استفاده کنیم
COPY requirements.txt .

# نصب وابستگی‌های پایتون
# با استفاده از pip وابستگی‌های پروژه را نصب می‌کنیم
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    # نصب gunicorn به عنوان سرور WSGI برای اجرای جنگو در محیط پروداکشن
    && pip install gunicorn

# کپی کل پروژه به داخل کانتینر
# حالا که وابستگی‌ها نصب شده‌اند، کل کد پروژه را کپی می‌کنیم
COPY . .

# ایجاد کاربر غیر روت برای اجرای برنامه
# اجرای برنامه با کاربر روت خطرناک است، پس یک کاربر با دسترسی محدود ایجاد می‌کنیم
RUN addgroup -S app && adduser -S app -G app

# تنظیم مجوزهای فایل‌ها و دایرکتوری‌ها
# اطمینان از اینکه کاربر app می‌تواند به فایل‌های مورد نیاز دسترسی داشته باشد
RUN mkdir -p $APP_HOME/staticfiles $APP_HOME/media $APP_HOME/logs \
    && chown -R app:app $APP_HOME

# کپی فایل‌های پیکربندی Nginx
# فایل nginx.conf را به مسیر پیکربندی Nginx کپی می‌کنیم
COPY ./config/nginx.conf /etc/nginx/conf.d/default.conf

# تنظیم کاربر برای اجرای دستورات بعدی
# از این پس، دستورات با کاربر app اجرا می‌شوند، نه کاربر روت
USER app

# اجرای اسکریپت راه‌اندازی
# این اسکریپت وظیفه راه‌اندازی Nginx، جمع‌آوری فایل‌های استاتیک و اجرای Gunicorn را بر عهده دارد
COPY --chown=app:app ./config/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# تنظیم دستور اجرا
# وقتی کانتینر اجرا می‌شود، این دستور اجرا می‌شود
ENTRYPOINT ["/entrypoint.sh"]

# افشای پورت 8000 برای دسترسی به برنامه
# این پورت برای دسترسی به برنامه جنگو استفاده می‌شود
EXPOSE 8000