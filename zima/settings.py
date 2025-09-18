"""
Django settings for zima project.
"""
import os
import socket
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv, UndefinedValueError

def is_running_in_docker():
    try:
        with open('/proc/1/cgroup', 'rt') as f:
            return 'docker' in f.read()
    except:
        return False

def is_production():
    env_value = os.environ.get('DJANGO_ENV', '').lower()
    if env_value:
        return env_value == 'production'

    hostname = socket.gethostname()
    return is_running_in_docker() or hostname in ['gunicorn', 'postgres', 'nginx']

DJANGO_ENV = 'production' if is_production() else 'development'
print(f"Detected environment: {DJANGO_ENV}")

BASE_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = '.env.production' if DJANGO_ENV == 'production' else '.env.local'
ENV_PATH = os.path.join(BASE_DIR, ENV_FILE)

if os.path.exists(ENV_PATH):
    print(f"Loading settings from {ENV_FILE}")
    from dotenv import load_dotenv
    load_dotenv(ENV_PATH)

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-key-for-development')

DEBUG = os.environ.get('DEBUG', 'True' if DJANGO_ENV == 'development' else 'False').lower() in ('true', '1', 't')

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'channels',
    'django.contrib.humanize',  # <--- مطمئن شوید این خط وجود دارد

    # My apps
    'users',
    'products',
    'orders',
    'cart',
    'pages',
    'chat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'chat.middleware.UserStatusMiddleware',
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# تنظیمات CORS
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:8000').split(',')
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'zima.urls'

# تنظیمات تمپلیت
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cart.context_processors.cart_items_count',
                'cart.context_processors.banners',
            ],
        },
    },
]

# تنظیمات رسانه‌ها و فایل‌های استاتیک
MEDIA_URL = os.environ.get('MEDIA_URL', '/media/')
MEDIA_ROOT = os.path.join(BASE_DIR, os.environ.get('MEDIA_ROOT', 'media'))

STATIC_URL = os.environ.get('STATIC_URL', '/static/')
STATIC_ROOT = os.path.join(BASE_DIR, os.environ.get('STATIC_ROOT', 'staticfiles'))
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# استفاده از WhiteNoise برای سرو فایل‌های استاتیک در محیط تولید
if DJANGO_ENV == 'production':
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

WSGI_APPLICATION = 'zima.wsgi.application'

# تنظیمات پایگاه داده - اصلاح شده برای Docker
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'zima'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'rezazh79'),
        'HOST': os.environ.get('DB_HOST', 'postgres'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'disable',
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 600,
    }
}

ASGI_APPLICATION = 'zima.asgi.application'
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis' if is_running_in_docker() else 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
            "capacity": 1500,
            "expiry": 10,
        },
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'CONNECTION_POOL_KWARGS': {'max_connections': 100},
            'RETRY_ON_TIMEOUT': True,
            'IGNORE_EXCEPTIONS': True,
        }
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
WEBSOCKET_URL = '/ws/'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = os.environ.get('LANGUAGE_CODE', 'fa-ir')
TIME_ZONE = os.environ.get('TIME_ZONE', 'Asia/Tehran')
USE_I18N = os.environ.get('USE_I18N', 'True').lower() in ('true', '1', 't')
USE_TZ = os.environ.get('USE_TZ', 'True').lower() in ('true', '1', 't')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

USE_L10N = True
USE_THOUSAND_SEPARATOR = True

# تنظیمات REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ) if DJANGO_ENV == 'production' else (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.environ.get('THROTTLE_ANON', '100/day'),
        'user': os.environ.get('THROTTLE_USER', '1000/day')
    },
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
}

# تنظیمات آپلود فایل
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024  # 12MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
PILLOW_FILE_TYPES = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']

AUTH_USER_MODEL = 'users.CustomUser'
ALLOWED_IMAGE_TYPES = [
    'image/jpeg', 'image/png', 'image/gif', 'image/bmp',
    'image/webp', 'image/svg+xml', 'image/tiff', 'image/heic', 'image/x-icon'
]

# تنظیمات JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=int(os.environ.get('SIMPLE_JWT_ACCESS_TOKEN_LIFETIME', '7'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.environ.get('SIMPLE_JWT_REFRESH_TOKEN_LIFETIME', '30'))),
    'ROTATE_REFRESH_TOKENS': os.environ.get('SIMPLE_JWT_ROTATE_REFRESH_TOKENS', 'True').lower() in ('true', '1', 't'),
    'BLACKLIST_AFTER_ROTATION': os.environ.get('SIMPLE_JWT_BLACKLIST_AFTER_ROTATION', 'True').lower() in ('true', '1', 't'),
    'UPDATE_LAST_LOGIN': os.environ.get('SIMPLE_JWT_UPDATE_LAST_LOGIN', 'True').lower() in ('true', '1', 't'),
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# تنظیمات ایمیل
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', f'Zima Shop <{os.environ.get("EMAIL_HOST_USER", "")}>')

# تنظیمات امنیتی - ساده شده برای Docker
ALLOWED_HOSTS = ['*']
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# تنظیمات CSRF
CSRF_TRUSTED_ORIGINS = [
    'https://zimabestshop.ir',
    'https://www.zimabestshop.ir',
    'http://localhost',
    'http://127.0.0.1',
    'http://localhost:8001',
]
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = 'Lax'

# تنظیمات لاگ - ساده شده برای Docker
USE_FILE_LOGGING = os.environ.get('USE_FILE_LOGGING', 'false').lower() == 'true'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

print(f"Settings loaded for {DJANGO_ENV} environment")
print("Django settings configured for Docker deployment")
# Override settings for Docker deployment
import os

# اجازه دادن به تمام میزبان‌ها
ALLOWED_HOSTS = ['*']

# تنظیم پایگاه داده برای Docker
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'zima'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'rezazh79'),
        'HOST': os.environ.get('DB_HOST', 'postgres'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'disable',
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 600,
    }
}

# غیرفعال کردن تنظیمات HTTPS در محیط توسعه
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

print("Django settings overridden for Docker deployment")

if DJANGO_ENV == 'production':
    # در داکر / سرور
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'amqp://guest:guest@rabbitmq:5672//')
else:
    # در محیط لوکال
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'amqp://guest:guest@localhost:5672//')

CELERY_RESULT_BACKEND = 'rpc://'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = USE_TZ

from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
     'cleanup-inactive-users': {
        'task': 'chat.tasks.cleanup_stale_online_statuses',
        'schedule': 60.0,
    },
    # هر ۱ دقیقه
    'force-offline-disconnected-users': {
        'task': 'chat.tasks.force_offline_disconnected_users',
        'schedule': 60.0,
    },
}