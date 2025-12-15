"""
Development settings for AgriMarket
Optimized for: local development, debugging, rapid iteration
"""

from .base import *

# ==================== DEBUG & SECURITY ====================
DEBUG = True
ALLOWED_HOSTS += ['localhost', '127.0.0.1', '0.0.0.0']  # ← + pour merge
CORS_ALLOW_ALL_ORIGINS = True

# ==================== DATABASE ====================
DATABASES['default'].update({
    'NAME': env('DB_NAME', default='agrimarket_dev'),
    'USER': env('DB_USER', default='agrimarket_user'),
    'PASSWORD': env('DB_PASSWORD', default='dev_password'),
    'HOST': env('DB_HOST', default='localhost'),
    'PORT': env('DB_PORT', default='5432'),
    'OPTIONS': {'sslmode': 'disable', 'connect_timeout': 10},
    'CONN_MAX_AGE': 0,
    'CONN_HEALTH_CHECKS': False,
})

# Option SQLite rapide (décommente si PG down)
# DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db_dev.sqlite3'}}

# ==================== EMAIL BACKEND ====================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'dev@agrimarket.local'

# ==================== CACHING ====================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'agrimarket-dev-cache',
        'KEY_PREFIX': 'dev_',  # ← Ajouté pour isoler
    }
}

# ==================== LOGGING VERBOSE ====================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{asctime} {levelname} {module} {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console'], 'level': 'DEBUG'},
    'loggers': {
        'django.db.backends': {'level': 'DEBUG', 'handlers': ['console']},
        'django.template': {'level': 'DEBUG', 'handlers': ['console']},
    },
}

# ==================== DJANGO DEBUG TOOLBAR ====================
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1', '10.0.2.2', 'localhost',]  # ← Ajouté pour toolbar visible (ex: Docker/VM)

def show_toolbar(request):
    return True

# DEBUG_TOOLBAR_CONFIG = {
#     'SHOW_TOOLBAR_CALLBACK': show_toolbar,
#     'RESULTS_CACHE_SIZE': 100,
# }

# ==================== CELERY ====================
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ==================== DÉPÔT DE FICHIERS ====================
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# ==================== SECURITÉ RELÂCHÉE ====================
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
X_FRAME_OPTIONS = 'SAMEORIGIN'

# ==================== PERFORMANCE DEV ====================
CELERY_BEAT_SCHEDULE = {}

