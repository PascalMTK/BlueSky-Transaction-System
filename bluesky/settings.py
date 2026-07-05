import os
import codecs
from pathlib import Path
from dotenv import load_dotenv

try:
    import dj_database_url
except ImportError:
    dj_database_url = None

BASE_DIR = Path(__file__).resolve().parent.parent

# Robust .env loader — bypasses python-dotenv BOM/parse issues entirely
def _load_env_safe():
    _path = BASE_DIR / '.env'
    try:
        with codecs.open(str(_path), 'r', 'utf-8-sig') as _f:
            for _line in _f:
                _line = _line.strip()
                if not _line or _line.startswith('#') or '=' not in _line:
                    continue
                _key, _, _val = _line.partition('=')
                _key = _key.strip()
                _val = _val.strip().strip('"').strip("'")
                if _key and _key not in os.environ:
                    os.environ[_key] = _val
    except Exception:
        load_dotenv(_path)

_load_env_safe()

# ── Security ────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get('SECRET_KEY', 'bluesky-django-secret-key-change-in-production')
DEBUG      = os.environ.get('DEBUG', 'False') == 'True'

_raw_hosts = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(',') if h.strip()]

_raw_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = (
    [o.strip() for o in _raw_origins.split(',') if o.strip()]
    if _raw_origins else
    ['https://*.ngrok-free.dev', 'https://*.ngrok-free.app', 'https://*.ngrok.io']
)

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',        # ← static files in production
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

# ── Database ─────────────────────────────────────────────────────────────────
# Railway / production: uses DATABASE_URL env var
# Local dev: falls back to local MySQL
_db_url = os.environ.get('DATABASE_URL', '')
_use_sqlite = os.environ.get('USE_SQLITE', 'False') == 'True'

if _use_sqlite:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
elif _db_url and dj_database_url:
    DATABASES = {'default': dj_database_url.parse(_db_url, conn_max_age=600)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'bluesky_transactions'),
            'USER': os.environ.get('DB_USER', 'root'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {'charset': 'utf8mb4'},
        }
    }

# ── Sessions ─────────────────────────────────────────────────────────────────
SESSION_ENGINE     = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400
SESSION_COOKIE_NAME = 'bluesky_session'

# ── Static & Media ────────────────────────────────────────────────────────────
STATIC_URL  = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── File upload limits ────────────────────────────────────────────────────────
DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Locale ────────────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'fr'
TIME_ZONE     = 'Africa/Kinshasa'
USE_I18N      = True
USE_TZ        = False

LOCALE_PATHS = [BASE_DIR / 'locale']

PASSWORD_HASHERS = [
    'core.hashers.LaravelBcryptHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# ── Cache (OTP storage) ───────────────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'bluesky_cache',
    }
}

# ── Site URL ────────────────────────────────────────────────────────────────
# Used to build absolute links to static assets in emails (e.g. the logo) —
# CID-embedded inline images render unreliably across mail clients/relays,
# a plain hosted URL is far more broadly compatible.
SITE_BASE_URL = os.environ.get('SITE_BASE_URL', 'https://pascal02.pythonanywhere.com')

# ── Email ─────────────────────────────────────────────────────────────────────
# Priority: SendGrid > Mailjet > explicit EMAIL_BACKEND > SMTP
if os.environ.get('SENDGRID_API_KEY'):
    EMAIL_BACKEND = 'core.email_backends.SendGridEmailBackend'
elif os.environ.get('MAILJET_API_KEY'):
    EMAIL_BACKEND = 'core.email_backends.MailjetEmailBackend'
else:
    EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST          = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS       = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_USE_SSL       = os.environ.get('EMAIL_USE_SSL', 'False') == 'True'
EMAIL_TIMEOUT       = 30
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = os.environ.get('EMAIL_FROM', 'BLUESKY Transactions <noreply@bluesky.com>')
SERVER_EMAIL        = os.environ.get('EMAIL_HOST_USER', 'noreply@bluesky.com')
OTP_EXPIRY_SECONDS  = 600
SENDGRID_API_KEY    = os.environ.get('SENDGRID_API_KEY', '')
BREVO_API_KEY       = os.environ.get('BREVO_API_KEY', '')
MAILJET_API_KEY     = os.environ.get('MAILJET_API_KEY', '')
MAILJET_API_SECRET  = os.environ.get('MAILJET_API_SECRET', '')

# ── Africa's Talking SMS ──────────────────────────────────────────────────────
AT_USERNAME    = os.environ.get('AT_USERNAME', 'sandbox')
AT_API_KEY     = os.environ.get('AT_API_KEY', '')
AT_SENDER_ID   = os.environ.get('AT_SENDER_ID', 'BLUESKY')
AT_SMS_ENABLED = os.environ.get('AT_SMS_ENABLED', 'False') == 'True'

# ── Production security (active when DEBUG=False) ─────────────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER    = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT        = True
    SESSION_COOKIE_SECURE      = True
    CSRF_COOKIE_SECURE         = True
    SECURE_BROWSER_XSS_FILTER  = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
