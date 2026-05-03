import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# .env local (optionnel). En prod Render, on utilise les variables Render.
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = os.environ.get("marketplace-s8vg.onrender.com", "127.0.0.1,localhost").split(",")

CSRF_TRUSTED_ORIGINS = []
_csrf = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "")
if _csrf.strip():
    CSRF_TRUSTED_ORIGINS = [x.strip() for x in _csrf.split(",") if x.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "accounts",
    "wallet",
    "products",
    "investments",
    "dashboard",
    "backoffice",
    "messaging",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # ✅ static files en prod
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ✅ DB: utilise DATABASE_URL si fourni, sinon SQLite local
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

# Mot de passe simple (dev). En prod tu pourras renforcer.
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 4},
    }
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Whitenoise storage (compress + cache)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "user_dashboard"
LOGOUT_REDIRECT_URL = "home"

# Option: si Render est derrière proxy https
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# MEDIA_URL pas obligatoire avec Cloudinary, mais tu peux laisser
MEDIA_URL = "/media/"


CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.environ.get("CLOUDINARY_CLOUD_NAME", ""),
    "API_KEY": os.environ.get("CLOUDINARY_API_KEY", ""),
    "API_SECRET": os.environ.get("CLOUDINARY_API_SECRET", ""),
}

DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"