FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    APP_HOME=/app

WORKDIR $APP_HOME

RUN apk update && apk add --no-cache --virtual .build-deps \
        postgresql-dev gcc python3-dev musl-dev libffi-dev \
    && apk add --no-cache \
        postgresql-client jpeg-dev zlib-dev gettext bash netcat-openbsd

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt gunicorn daphne \
    && apk del .build-deps

# ایجاد کاربر قبل از کپی کردن فایل‌ها
RUN addgroup -S app && adduser -S app -G app

COPY . .

# تنظیم مجوزها - اصلاح شده
RUN mkdir -p staticfiles media \
    && chown -R app:app /app \
    && chmod -R 755 /app \
    && chmod -R 777 /app/staticfiles \
    && chmod -R 777 /app/media

COPY --chown=app:app ./config/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER app

ENTRYPOINT ["/entrypoint.sh"]