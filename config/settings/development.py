"""
Development settings for AgriMarket
"""

from .base import *

# ==================== DEBUG & SECURITY ====================
DEBUG = True
ALLOWED_HOSTS += ['localhost', '127.0.0.1', '0.0.0.0', '192.168.1.*']  # Pour le réseau local
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ==================== DATABASE ====================
# # Utiliser SQLite pour le développement pour plus de simplicité
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# ==================== EMAIL BACKEND ====================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'dev@agribusiness.local'

# ==================== CACHING ====================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'agribusiness-dev-cache',
        'KEY_PREFIX': 'dev_',
    }
}

# ==================== CELERY ====================
# CELERY_BROKER_URL = 'memory://'  # Utiliser le broker en mémoire pour le développement
CELERY_TASK_ALWAYS_EAGER = True  # Exécuter les tâches de manière synchrone
CELERY_TASK_EAGER_PROPAGATES = True

# Désactiver les tâches périodiques en développement sauf celles essentielles
CELERY_BEAT_SCHEDULE = {
    'monitor-system-health': {
        'task': 'tasks.periodic_tasks.monitor_system_health',
        'schedule': 300.0,  # Toutes les 5 minutes
    },
}

# ==================== LOGGING VERBOSE ====================
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['celery']['level'] = 'DEBUG'
LOGGING['loggers']['tasks']['level'] = 'DEBUG'

# Ajouter un handler de fichier pour le développement
LOGGING['handlers']['dev_file'] = {
    'level': 'DEBUG',
    'class': 'logging.FileHandler',
    'filename': BASE_DIR / 'logs' / 'development.log',
    'formatter': 'verbose'
}
LOGGING['loggers']['django']['handlers'].append('dev_file')

# ==================== DJANGO DEBUG TOOLBAR ====================
INSTALLED_APPS += [
    # 'debug_toolbar',
    'django_extensions',
]

# MIDDLEWARE += [
#     'debug_toolbar.middleware.DebugToolbarMiddleware',
# ]

# INTERNAL_IPS = [
#     '127.0.0.1',
#     'localhost',
#     '0.0.0.0',
# ]

# DEBUG_TOOLBAR_CONFIG = {
#     'SHOW_TOOLBAR_CALLBACK': lambda request: True,
#     'RESULTS_STORE_SIZE': 100,
# }

# ==================== DÉPÔT DE FICHIERS ====================
MEDIA_ROOT = BASE_DIR / 'media_dev'
STATICFILES_DIRS += [
    BASE_DIR / 'static_dev',
]

# ==================== SECURITÉ RELÂCHÉE ====================
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
X_FRAME_OPTIONS = 'SAMEORIGIN'

# ==================== PERFORMANCE DEV ====================
# Désactiver le cache des templates pour le développement
TEMPLATES[0]['OPTIONS']['debug'] = True

# ==================== DJANGO EXTENSIONS ====================
# Configuration pour django-extensions
SHELL_PLUS = "ipython"
SHELL_PLUS_PRINT_SQL = True

# ==================== TEST CONFIGURATION ====================
# Configuration pour les tests
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# ==================== DEVELOPMENT TOOLS ====================
# Activer les outils de développement
ENABLE_DEV_TOOLS = True

# Configuration du serveur de développement
DEVELOPMENT_MODE = True

# ==================== CORS POUR LE DEV ====================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    # "http://localhost:3000",
    # "http://127.0.0.1:3000",
]

# ==================== EMAIL DEV CONFIG ====================
# Configurer un serveur SMTP de développement
if EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
    EMAIL_HOST = 'localhost'
    EMAIL_PORT = 1025  # MailHog ou similaire
    EMAIL_USE_TLS = False

# ==================== CELERY DEV CONFIG ====================
# Pour le développement, on peut utiliser des workers simplifiés
CELERY_WORKER_CONCURRENCY = 2
CELERY_WORKER_PREFETCH_MULTIPLIER = 1


# """
# Development settings for AgriMarket
# Optimized for: local development, debugging, rapid iteration
# """

# from .base import *

# # ==================== DEBUG & SECURITY ====================
# DEBUG = True
# ALLOWED_HOSTS += ['localhost', '127.0.0.1', '0.0.0.0']  # ← + pour merge
# CORS_ALLOW_ALL_ORIGINS = True

# # ==================== DATABASE ====================
# DATABASES['default'].update({
#     'NAME': env('DB_NAME', default='agrimarket_dev'),
#     'USER': env('DB_USER', default='agrimarket_user'),
#     'PASSWORD': env('DB_PASSWORD', default='dev_password'),
#     'HOST': env('DB_HOST', default='localhost'),
#     'PORT': env('DB_PORT', default='5432'),
#     'OPTIONS': {'sslmode': 'disable', 'connect_timeout': 10},
#     'CONN_MAX_AGE': 0,
#     'CONN_HEALTH_CHECKS': False,
# })

# # Option SQLite rapide (décommente si PG down)
# # DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db_dev.sqlite3'}}

# # ==================== EMAIL BACKEND ====================
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# DEFAULT_FROM_EMAIL = 'dev@agrimarket.local'

# # ==================== CACHING ====================
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         'LOCATION': 'agrimarket-dev-cache',
#         'KEY_PREFIX': 'dev_',  # ← Ajouté pour isoler
#     }
# }

# # ==================== LOGGING VERBOSE ====================
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {'format': '{asctime} {levelname} {module} {message}', 'style': '{'},
#     },
#     'handlers': {
#         'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
#     },
#     'root': {'handlers': ['console'], 'level': 'DEBUG'},
#     'loggers': {
#         'django.db.backends': {'level': 'DEBUG', 'handlers': ['console']},
#         'django.template': {'level': 'DEBUG', 'handlers': ['console']},
#     },
# }

# # ==================== DJANGO DEBUG TOOLBAR ====================
# # INSTALLED_APPS += ['debug_toolbar']
# # MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# # INTERNAL_IPS = ['127.0.0.1', '10.0.2.2', 'localhost',]  # ← Ajouté pour toolbar visible (ex: Docker/VM)

# def show_toolbar(request):
#     return True

# # DEBUG_TOOLBAR_CONFIG = {
# #     'SHOW_TOOLBAR_CALLBACK': show_toolbar,
# #     'RESULTS_CACHE_SIZE': 100,
# # }

# # ==================== CELERY ====================
# CELERY_TASK_ALWAYS_EAGER = True
# CELERY_TASK_EAGER_PROPAGATES = True

# # ==================== DÉPÔT DE FICHIERS ====================
# DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# # ==================== SECURITÉ RELÂCHÉE ====================
# SECURE_SSL_REDIRECT = False
# SESSION_COOKIE_SECURE = False
# CSRF_COOKIE_SECURE = False
# SECURE_BROWSER_XSS_FILTER = False
# SECURE_CONTENT_TYPE_NOSNIFF = False
# X_FRAME_OPTIONS = 'SAMEORIGIN'

# # ==================== PERFORMANCE DEV ====================
# CELERY_BEAT_SCHEDULE = {}

