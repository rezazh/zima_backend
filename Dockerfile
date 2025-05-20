FROM python:3.10-slim

# تنظیم متغیرهای محیطی
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=zima.settings

# ایجاد و تنظیم دایرکتوری کاری
WORKDIR /app

# نصب وابستگی‌ها
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# کپی فایل requirements و نصب وابستگی‌ها
COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# کپی کل پروژه
COPY . /app/

# جمع‌آوری فایل‌های استاتیک
RUN python manage.py collectstatic --noinput

# اجرای اپلیکیشن با gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "zima.wsgi:application"]