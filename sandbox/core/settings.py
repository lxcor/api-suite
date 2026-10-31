import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent   # sandbox/
REPO_DIR = BASE_DIR.parent                          # repo root

# Load .env from repo root without overriding existing env vars
_env_file = REPO_DIR / '.env'
if _env_file.exists():
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _key, _, _val = _line.partition('=')
                os.environ.setdefault(_key.strip(), _val.strip())

DEBUG = os.environ.get('DJANGO_DEBUG', '0') == '1'

if not DEBUG and 'DJANGO_SECRET_KEY' not in os.environ:
    raise RuntimeError(
        'DJANGO_SECRET_KEY must be set when DEBUG is off. '
        'Add it to .env or set DJANGO_DEBUG=1 for local development.'
    )

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-only-insecure-key-do-not-use-in-production')

_hosts_env = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [h.strip() for h in _hosts_env.split(',') if h.strip()] or ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'rest_framework',
    'docca',
    'reggi',
    'kotta',
    'billa',
    'romma',
    'tools',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'kotta.middleware.KottaMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'
WSGI_APPLICATION = 'core.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'romma.context_processors.home_settings',
                'reggi.context_processors.reggi_settings',
                'billa.context_processors.billa_settings',
            ],
        },
    },
]

if os.environ.get('DJANGO_DB_NAME'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ['DJANGO_DB_NAME'],
            'USER': os.environ.get('DJANGO_DB_USER', ''),
            'PASSWORD': os.environ.get('DJANGO_DB_PASSWORD', ''),
            'HOST': os.environ.get('DJANGO_DB_HOST', 'localhost'),
            'PORT': os.environ.get('DJANGO_DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'localhost'
    EMAIL_PORT = 25

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

FIXTURE_DIRS = [BASE_DIR / 'fixtures']

USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'

SESSION_COOKIE_NAME = 'sessionid_api'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'reggi.authentication.ApiKeyAuthentication',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'kotta.throttle.AnonEndpointThrottle',
        'kotta.throttle.TierThrottle',
        'billa.throttle.BillerThrottle',
    ],
    'EXCEPTION_HANDLER': 'kotta.exceptions.kotta_exception_handler',
}

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    _non_local = [h for h in ALLOWED_HOSTS if h not in ('localhost', '127.0.0.1')]
    if _non_local:
        CSRF_TRUSTED_ORIGINS = [f'https://{h}' for h in _non_local]
