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
    gcc \
    python3-dev \
    musl-dev \
    jpeg-dev \
    zlib-dev \
    libffi-dev \
    gettext \
    nginx

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn

COPY . .

RUN addgroup -S app && adduser -S app -G app

RUN mkdir -p $APP_HOME/staticfiles $APP_HOME/media $APP_HOME/logs \
    && chown -R app:app $APP_HOME

COPY ./config/nginx.conf /etc/nginx/conf.d/default.conf

USER app

COPY --chown=app:app ./config/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 8000