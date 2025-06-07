FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    APP_HOME=/app

WORKDIR $APP_HOME

RUN apk update \
    && apk add --no-cache \
    postgresql-dev \
    postgresql-client \  # اضافه کردن کلاینت PostgreSQL
    gcc \
    python3-dev \
    musl-dev \
    jpeg-dev \
    zlib-dev \
    libffi-dev \
    gettext \
    bash \  # اضافه کردن bash برای اسکریپت‌های پیچیده‌تر
    netcat-openbsd \  # برای بررسی اتصال به پورت‌ها
    nginx

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn

# کپی اسکریپت‌های مدیریت مایگریشن
COPY ./config/migration_utils.py /app/config/
COPY ./config/db_cleanup.sql /app/config/

# کپی کل پروژه
COPY . .

RUN addgroup -S app && adduser -S app -G app

RUN mkdir -p $APP_HOME/staticfiles $APP_HOME/media $APP_HOME/logs \
    && chown -R app:app $APP_HOME

COPY ./config/nginx.conf /etc/nginx/conf.d/default.conf

# اطمینان از دسترسی به اسکریپت‌های entrypoint
COPY --chown=app:app ./config/gunicorn-entrypoint.sh /app/config/
COPY --chown=app:app ./config/django-entrypoint.sh /app/config/
RUN chmod +x /app/config/gunicorn-entrypoint.sh /app/config/django-entrypoint.sh

USER app

ENTRYPOINT ["/app/config/gunicorn-entrypoint.sh"]