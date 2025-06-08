FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    APP_HOME=/app

WORKDIR $APP_HOME

# نصب وابستگی‌های سیستم در یک لایه
RUN apk update && apk add --no-cache --virtual .build-deps \
        postgresql-dev gcc python3-dev musl-dev libffi-dev \
    && apk add --no-cache \
        postgresql-client jpeg-dev zlib-dev gettext bash netcat-openbsd

# کپی و نصب requirements
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt gunicorn daphne \
    && apk del .build-deps

# کپی کد
COPY . .

# تنظیم کاربر و مجوزها
RUN addgroup -S app && adduser -S app -G app \
    && mkdir -p staticfiles media logs \
    && chown -R app:app /app

COPY --chown=app:app ./config/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER app

ENTRYPOINT ["/entrypoint.sh"]