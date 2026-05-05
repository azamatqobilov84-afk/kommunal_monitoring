"""
Django sozlamalari — Kommunal to'lovlar monitoringi loyihasi.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-kommunal-monitoring-dev-key-change-in-prod-9f3k2l'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.user_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 4}},
]

AUTH_USER_MODEL = 'core.User'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Mock SMS — kodlar terminalga chop etiladi
MOCK_SMS_TO_CONSOLE = True
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 kun


# ==========================================================================
# UNIVERSAL PRODUCTION SOZLAMALARI — Render / Fly.io / Railway
# ==========================================================================
import os as _os

IS_PRODUCTION = bool(
    _os.environ.get('RENDER') or
    _os.environ.get('FLY_APP_NAME') or
    _os.environ.get('RAILWAY_PROJECT_ID')
)

if IS_PRODUCTION:
    DEBUG = False
    SECRET_KEY = _os.environ.get('DJANGO_SECRET_KEY', SECRET_KEY)

    # ----- ALLOWED_HOSTS — barcha hostlarni qabul qilish (demo uchun) -----
    ALLOWED_HOSTS = ['*']

    # ----- CSRF -----
    CSRF_TRUSTED_ORIGINS = [
        'https://*.onrender.com',
        'https://*.fly.dev',
        'https://*.up.railway.app',
        'https://*.railway.app',
    ]
    if _os.environ.get('CUSTOM_DOMAIN'):
        CSRF_TRUSTED_ORIGINS.append(f"https://{_os.environ['CUSTOM_DOMAIN']}")

    # ----- DATABASE -----
    _db_url = _os.environ.get('DATABASE_URL')
    if _db_url:
        # Render / Railway — PostgreSQL beradi
        try:
            import dj_database_url
            DATABASES['default'] = dj_database_url.parse(_db_url, conn_max_age=600)
        except ImportError:
            pass
    elif _os.environ.get('FLY_APP_NAME'):
        # Fly.io — SQLite + Volume
        DATABASES['default']['NAME'] = '/data/db.sqlite3'

    # ----- STATIC FILES (WhiteNoise) -----
    if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
        MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    # CompressedStaticFilesStorage — Manifest emas! (xatolarni oldini oladi)
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

    # ----- MEDIA -----
    if _os.environ.get('FLY_APP_NAME'):
        MEDIA_ROOT = '/data/media'

    # ----- SECURITY -----
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'