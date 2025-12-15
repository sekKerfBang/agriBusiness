"""
Production settings for AgriMarket
Optimized for: sécurité, performance, scalabilité
"""

from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# ==================== DEBUG & SECURITY ====================
DEBUG = False
ALLOWED_HOSTS += env.list('ALLOWED_HOSTS', default=['agrimarket.com', 'www.agrimarket.com'])

SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_TRUSTED_ORIGINS = [f'https://{host}' for host in ALLOWED_HOSTS]

# ==================== DATABASE ====================
DATABASES['default'].update({
    'OPTIONS': {
        'sslmode': 'require',
        'connect_timeout': 5,
        'sslrootcert': env('DB_SSL_ROOT_CERT', default=''),
        'sslcert': env('DB_SSL_CERT', default=''),
        'sslkey': env('DB_SSL_KEY', default=''),
    },
    'CONN_MAX_AGE': 600,
    'CONN_HEALTH_CHECKS': True,
})

# ==================== EMAIL ====================
EMAIL_BACKEND = 'anymail.backends.sendgrid.EmailBackend'
ANYMAIL.update({
    'SENDGRID_API_KEY': env('SENDGRID_API_KEY'),
    'SENDGRID_GENERATE_MESSAGE_ID': True,
})
DEFAULT_FROM_EMAIL = 'noreply@agrimarket.com'
SERVER_EMAIL = 'alerts@agrimarket.com'

# ==================== CACHING ====================
try:
    import django_redis  # ← Guard : assume installé
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',  # ← Corrigé backend
            'LOCATION': env('REDIS_URL', default='redis://localhost:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
            },
            'KEY_PREFIX': 'agrimarket_prod',
            'TIMEOUT': 3600,
        }
    }
except ImportError:
    CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}  # Fallback safe

# ==================== LOGGING ====================
try:
    from pythonjsonlogger import jsonlogger  # ← Assume installé
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {'format': '{asctime} {levelname} {name} {module} {process:d} {thread:d} {message}', 'style': '{'},
            'json': {'()': jsonlogger.JsonFormatter, 'format': '%(asctime) %(levelname) %(name) %(module) %(message)'},
        },
        'handlers': {
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': BASE_DIR / 'logs' / 'agrimarket.log',  # ← Path relatif à BASE_DIR
                'maxBytes': 1024 * 1024 * 15,
                'backupCount': 10,
                'formatter': 'verbose',
            },
            'console': {'class': 'logging.StreamHandler', 'formatter': 'json'},
        },
        'root': {'handlers': ['console'], 'level': 'INFO'},
        'loggers': {
            'django': {'handlers': ['file', 'console'], 'level': 'INFO', 'propagate': False},
            'django.server': {'level': 'INFO', 'handlers': ['console'], 'propagate': False},
            'celery': {'handlers': ['console'], 'level': 'INFO'},
        },
    }
except ImportError:
    # Fallback simple
    LOGGING = {'version': 1, 'disable_existing_loggers': False, 'handlers': {'console': {'class': 'logging.StreamHandler'}}, 'root': {'handlers': ['console'], 'level': 'INFO'}}

# ==================== SENTRY ====================
SENTRY_DSN = env('SENTRY_DSN')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=False,
        environment='production',
    )

# ==================== CELERY ====================
CELERY_TASK_ALWAYS_EAGER = False
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_POOL = 'prefork'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# ==================== DÉPÔT DE FICHIERS (S3 guard) ====================
if env.bool('USE_S3', default=False) and all(env(k) for k in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_STORAGE_BUCKET_NAME']):
    import boto3  # Assume installé via storages
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='eu-west-1')  # ← Ajouté pour FR
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
    STATIC_ROOT = BASE_DIR / 'staticfiles_prod'

# ==================== BACKUP (assume django-dbbackup installé) ====================
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': BASE_DIR / 'backups'}
DBBACKUP_CLEANUP_KEEP = 5

# ==================== OPTIMISATIONS ====================
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# Compression (assume django-compressor installé)
COMPRESS_ENABLED = env.bool('COMPRESS_ENABLED', default=True)
COMPRESS_OFFLINE = True

# ==================== RATE LIMITING ====================
REST_FRAMEWORK.setdefault('DEFAULT_THROTTLE_CLASSES', []).extend([
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle',
])
REST_FRAMEWORK.setdefault('DEFAULT_THROTTLE_RATES', {}) = {
    'anon': '100/hour',
    'user': '1000/hour',
}

# ==================== CORS ====================
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'https://agrimarket.com',
    'https://www.agrimarket.com',
])
CORS_ALLOW_CREDENTIALS = True

# Session pour dashboards (timeout 2h pour entreprises)
SESSION_COOKIE_AGE = 7200
SESSION_SAVE_EVERY_REQUEST = True


# """
# Production settings for AgriMarket
# Optimized for: sécurité, performance, scalabilité
# """

# from .base import *
# import sentry_sdk
# from sentry_sdk.integrations.django import DjangoIntegration

# # ==================== DEBUG & SECURITY ====================
# DEBUG = False
# ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['agrimarket.com', 'www.agrimarket.com'])

# # HSTS (Force HTTPS)
# SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_HSTS_SECONDS = 31536000  # 1 an
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# # Protection contre XSS et clickjacking
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# X_FRAME_OPTIONS = 'DENY'

# # ==================== DATABASE ====================
# # Connexions chiffrées et poolées
# DATABASES = {
#     'default': {
#         **DATABASES['default'],  # Hérite de base.py
#         'OPTIONS': {
#             'sslmode': 'require',
#             'connect_timeout': 5,
#             # Certificats SSL pour RDS/AWS
#             'sslrootcert': env('DB_SSL_ROOT_CERT', default='/app/certs/rds-ca.pem'),
#             'sslcert': env('DB_SSL_CERT', default=''),
#             'sslkey': env('DB_SSL_KEY', default=''),
#         },
#         'CONN_MAX_AGE': 600,  # 10 minutes
#         'CONN_HEALTH_CHECKS': True,
#     }
# }

# # ==================== EMAIL ====================
# # Email vrai avec SendGrid/AWS SES
# EMAIL_BACKEND = 'anymail.backends.sendgrid.EmailBackend'
# ANYMAIL = {
#     'SENDGRID_API_KEY': env('SENDGRID_API_KEY'),
#     'SENDGRID_GENERATE_MESSAGE_ID': True,
# }
# DEFAULT_FROM_EMAIL = 'noreply@agrimarket.com'
# SERVER_EMAIL = 'alerts@agrimarket.com'

# # ==================== CACHING ====================
# # Cache Redis en production
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': env('REDIS_URL', default='redis://redis:6379/1'),
#         'OPTIONS': {
#             'db': 1,
#             'parser_class': 'redis.connection.PythonParser',
#             'pool_class': 'redis.BlockingConnectionPool',
#             'pool_kwargs': {'max_connections': 50, 'timeout': 20},
#         },
#         'KEY_PREFIX': 'agrimarket_prod',
#         'TIMEOUT': 3600,  # 1 heure
#     }
# }

# # ==================== LOGGING ====================
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '{asctime} {levelname} {name} {module} {process:d} {thread:d} {message}',
#             'style': '{',
#         },
#         'json': {
#             '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
#             'format': '%(asctime) %(levelname) %(name) %(module) %(message)',
#         },
#     },
#     'handlers': {
#         'file': {
#             'class': 'logging.handlers.RotatingFileHandler',
#             'filename': '/var/log/agrimarket/django.log',
#             'maxBytes': 1024 * 1024 * 15,  # 15 MB
#             'backupCount': 10,
#             'formatter': 'verbose',
#         },
#         'console': {
#             'class': 'logging.StreamHandler',
#             'formatter': 'json',
#         },
#     },
#     'root': {
#         'handlers': ['console'],
#         'level': 'INFO',
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['file', 'console'],
#             'level': 'INFO',
#             'propagate': False,
#         },
#         'django.server': {
#             'level': 'INFO',
#             'handlers': ['console'],
#             'propagate': False,
#         },
#         'celery': {
#             'handlers': ['console'],
#             'level': 'INFO',
#         },
#     },
# }

# # ==================== SENTRY MONITORING ====================
# SENTRY_DSN = env('SENTRY_DSN', default=None)
# if SENTRY_DSN:
#     sentry_sdk.init(
#         dsn=SENTRY_DSN,
#         integrations=[DjangoIntegration()],
#         traces_sample_rate=1.0,  # 100% des transactions
#         send_default_pii=False,
#         environment='production',
#     )

# # ==================== CELERY ====================
# CELERY_TASK_ALWAYS_EAGER = False
# CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # Restart worker après 1000 tâches
# CELERY_WORKER_POOL = 'prefork'  # Ou 'gevent' pour async
# CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# # ==================== DÉPÔT DE FICHIERS ====================
# # AWS S3 pour static & media
# AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME = 'agrimarket-prod'
# AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
# AWS_DEFAULT_ACL = 'public-read'

# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

# # ==================== DATABASE BACKUP ====================
# # Backup automatique vers S3
# DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
# DBBACKUP_STORAGE_OPTIONS = {'location': '/backups/'}
# DBBACKUP_CLEANUP_KEEP = 5  # Garde les 5 derniers backups

# # ==================== OPTIMISATIONS DJANGO ====================
# # Template caching
# TEMPLATES[0]['OPTIONS']['loaders'] = [
#     ('django.template.loaders.cached.Loader', [
#         'django.template.loaders.filesystem.Loader',
#         'django.template.loaders.app_directories.Loader',
#     ]),
# ]

# # Compression et minification
# COMPRESS_ENABLED = True
# COMPRESS_OFFLINE = True

# # ==================== RATE LIMITING ====================
# # Protège l'API contre les abus
# REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
#     'rest_framework.throttling.AnonRateThrottle',
#     'rest_framework.throttling.UserRateThrottle'
# ]
# REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
#     'anon': '100/hour',
#     'user': '1000/hour'
# }

# # ==================== CORS EN PRODUCTION ====================
# CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
#     'https://agrimarket.com',
#     'https://www.agrimarket.com',
# ])
# CORS_ALLOW_CREDENTIALS = True