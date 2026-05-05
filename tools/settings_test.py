SECRET_KEY = 'tools-test-secret-key'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'tools',
]

USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

TOOLS_HEALTH_CHECKS = ['db']
