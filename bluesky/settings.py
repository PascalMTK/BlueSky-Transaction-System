import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = 'bluesky-django-secret-key-change-in-production'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'core.middleware.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'core.middleware.AuthMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bluesky.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'bluesky.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'bluesky_transactions',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

# Sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24h
SESSION_COOKIE_NAME = 'bluesky_session'

# Static & Media
STATIC_URL  = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Locale
LANGUAGE_CODE = 'fr'
TIME_ZONE     = 'Africa/Kinshasa'
USE_I18N      = True
USE_TZ        = False

PASSWORD_HASHERS = [
    'core.hashers.LaravelBcryptHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

LOCALE_PATHS = [BASE_DIR / 'locale']

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# ── Cache (OTP storage) ────────────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'bluesky-otp',
    }
}

# ── Email ──────────────────────────────────────────────────────────────────
EMAIL_BACKEND    = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST       = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT       = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS    = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER  = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = os.environ.get('EMAIL_FROM', 'BLUESKY Transactions <noreply@bluesky.com>')
OTP_EXPIRY_SECONDS  = 600  # 10 minutes

# ── Africa's Talking SMS ───────────────────────────────────────────────────
AT_USERNAME   = os.environ.get('AT_USERNAME', 'sandbox')
AT_API_KEY    = os.environ.get('AT_API_KEY', '')
AT_SENDER_ID  = os.environ.get('AT_SENDER_ID', 'BLUESKY')
AT_SMS_ENABLED = os.environ.get('AT_SMS_ENABLED', 'False') == 'True'
