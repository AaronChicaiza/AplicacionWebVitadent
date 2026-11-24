"""Configuración del proyecto Django VitaDent."""

import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() == "true"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-vitadent-solo-desarrollo-local")
if not DEBUG and (
    len(os.environ.get("DJANGO_SECRET_KEY", "")) < 50
    or SECRET_KEY.startswith(("django-insecure-", "cambiar", "solo-desarrollo", "build-only"))
):
    raise ImproperlyConfigured("Configura DJANGO_SECRET_KEY aleatoria de al menos 50 caracteres antes de producción.")
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "web.apps.WebConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "web.middleware.LimiteSolicitudesMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "web.middleware.CabecerasSeguridadMiddleware",
    "web.middleware.CambioClaveInicialMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "vitadent.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "vitadent.wsgi.application"
ASGI_APPLICATION = "vitadent.asgi.application"


LANGUAGE_CODE = "es-ec"
TIME_ZONE = "America/Guayaquil"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "web" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
if not DEBUG:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if os.environ.get("POSTGRES_DB"):
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ.get("POSTGRES_USER", ""),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }}
else:
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "vitadent-limites-locales",
    }
}
if os.environ.get("REDIS_URL"):
    CACHES["default"] = {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ["REDIS_URL"],
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": "vitadent",
    }

if not DEBUG and not os.environ.get("POSTGRES_DB"):
    raise ImproperlyConfigured("Configura PostgreSQL con POSTGRES_DB para producción.")
if not DEBUG and not os.environ.get("REDIS_URL"):
    raise ImproperlyConfigured("Configura REDIS_URL para límites distribuidos en producción.")

LOGIN_URL = "acceso_personal"
LOGIN_REDIRECT_URL = "gestion_inicio"
LOGOUT_REDIRECT_URL = "inicio"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

RASA_REST_URL = os.environ.get("VITADENT_RASA_URL", "")
VITADENT_RASA_TOKEN = os.environ.get("VITADENT_RASA_TOKEN", "")
VITADENT_WHATSAPP_NUMBER = os.environ.get("VITADENT_WHATSAPP_NUMBER", "")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "")
WHATSAPP_APP_SECRET = os.environ.get("WHATSAPP_APP_SECRET", "")
WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_GRAPH_API_VERSION = os.environ.get("WHATSAPP_GRAPH_API_VERSION", "v25.0")
VITADENT_CONVERSATION_RETENTION_DAYS = int(os.environ.get("VITADENT_CONVERSATION_RETENTION_DAYS", "30"))
VITADENT_MIN_CANCEL_HOURS = int(os.environ.get("VITADENT_MIN_CANCEL_HOURS", "0"))

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "120/hour", "user": "1200/hour"},
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "API VitaDent",
    "DESCRIPTION": "API de catálogo, disponibilidad, citas y operación del personal.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "ENUM_NAME_OVERRIDES": {
        "CitaEstadoEnum": "web.models.Cita.Estado",
        "ConversacionEstadoEnum": "web.models.Conversacion.Estado",
        "NotificacionEstadoEnum": "web.models.Notificacion.Estado",
    },
}
SWAGGER_UI_DIST = "SIDECAR"
REDOC_DIST = "SIDECAR"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 3600
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "True").lower() == "true"
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    if os.environ.get("DJANGO_TRUST_PROXY", "False").lower() == "true":
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
