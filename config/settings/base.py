"""
Django settings for config project.
"""

import environ
from pathlib import Path
from datetime import timedelta
from functools import partial
from celery.schedules import crontab  # Ajout important

# Build paths
env = environ.Env()
environ.Env.read_env(Path(__file__).resolve().parent.parent.parent / '.env')
# env = environ.Env()
# environ.Env.read_env(Path(__file__).resolve().parent.parent.parent / '.env')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
APPS_DIR = BASE_DIR / "apps"

# Partial functions
static_path = partial(Path.joinpath, BASE_DIR)
media_path = partial(Path.joinpath, BASE_DIR)
jwt_timedelta = partial(timedelta)

# Security
SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# Applications
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'anymail',
    'django_celery_beat',
    'django_celery_results',
    'django_htmx',
    
    # Local apps
    'apps.utilisateur',
    'apps.products',
    'apps.orders',
    'apps.marketplace',
    'apps.dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'config.urls'

# Custom user
AUTH_USER_MODEL = 'utilisateur.Utilisateur'
LOGIN_REDIRECT_URL = 'marketplace/home/'
LOGOUT_REDIRECT_URL = 'marketplace/home/'
LOGIN_URL = '/login/'

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
                'config.context_processors.unread_notifications',
                'apps.orders.context_processors.cart_context',
                "marketplace.context_processors.cart_context",
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# # Database (PostgreSQL avec options avancées)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env.int('DB_PORT', default='5432'),
        'OPTIONS': {
            'connect_timeout': 10,
            'sslmode': 'require' if env.bool('DB_SSL', default=False) else 'disable',
        },
        'CONN_MAX_AGE': env.int('DB_CONN_MAX_AGE', default=0),
        'CONN_HEALTH_CHECKS': True,  # Django 6.0 OK
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Afrique/Guinée'
USE_I18N = True
USE_TZ = True
USE_L10N = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = static_path('staticfiles')
STATICFILES_DIRS = [
    APPS_DIR / "marketplace" / "static",
    APPS_DIR / "dashboard" / "static",
]

MEDIA_URL = '/media/'
MEDIA_ROOT = media_path('media')
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': env.int('API_PAGE_SIZE', default=20),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': jwt_timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': jwt_timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Celery Configuration
# CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')  # ou 'django-db'

# CELERY_RESULT_BACKEND = 'django-db'  # Utilise la base de données Django
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER', default=False)
CELERY_TASK_EAGER_PROPAGATES = True


# Configuration des files d'attente
# CELERY_TASK_ROUTES = {
#     'tasks.email_tasks.send_order_confirmation_task': {'queue': 'high_priority'},
#     'tasks.email_tasks.send_password_reset_task': {'queue': 'high_priority'},
#     'tasks.notification_tasks.process_low_stock_alerts': {'queue': 'high_priority'},
#     'tasks.email_tasks.send_daily_sales_report': {'queue': 'reports'},
#     'tasks.email_tasks.send_bulk_newsletter_task': {'queue': 'bulk_emails'},
#     'tasks.product_tasks.generate_product_catalog_pdf': {'queue': 'heavy_tasks'},
#     'tasks.periodic_tasks.*': {'queue': 'maintenance'},
# }

# Email Configuration (avec fallback)
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@agribusiness.com')

# SendGrid pour la production
if EMAIL_BACKEND == 'anymail.backends.sendgrid.EmailBackend':
    ANYMAIL = {
        "SENDGRID_API_KEY": env('SENDGRID_API_KEY', default=''),
    }

# SMTP fallback
if EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
    EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
    EMAIL_PORT = env.int('EMAIL_PORT', default=587)
    EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
    EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

# Security settings
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=False)
CSRF_COOKIE_HTTPONLY = env.bool('CSRF_COOKIE_HTTPONLY', default=True)
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=['http://127.0.0.1:8000', 'http://localhost:8000'])

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'agribusiness',
    }
}

# Password reset timeout
PASSWORD_RESET_TIMEOUT = 259200  # 3 jours en secondes

# Stripe Configuration
STRIPE_PUBLIC_KEY = env('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')

# File Upload Configuration
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_COOKIE_AGE = 1209600  # 2 semaines en secondes
SESSION_SAVE_EVERY_REQUEST = True

# Logging Configuration
# ces logging servent a logger les erreurs et infos importantes de l'application django et celery dans la console et dans des fichiers logs pour faciliter le debug et le suivi de l'application 
# afin d'ameliorer la maintenance et la resolution des problemes en production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django_errors.log',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'tasks': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Backup directory
# ces lignes suivent nous permettent de creer des dossiers logs, backups et catalogs s'ils n'existent pas deja pour eviter des erreurs lors de l'ecriture de fichiers dans ces dossiers
import os
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
os.makedirs(BASE_DIR / 'backups', exist_ok=True)
os.makedirs(BASE_DIR / 'catalogs', exist_ok=True)




# """
# Django settings for config project.
# Generated by 'django-admin startproject' using Django 6.0.
# For more information, see https://docs.djangoproject.com/en/6.0/topics/settings/
# """

# import environ
# from pathlib import Path
# from datetime import timedelta
# from functools import partial

# # Build paths inside the project like this: BASE_DIR / 'subdir'.
# env = environ.Env()
# environ.Env.read_env(Path(__file__).resolve().parent.parent.parent / '.env')  # .env à la root

# BASE_DIR = Path(__file__).resolve().parent.parent.parent
# APPS_DIR = BASE_DIR / "apps"

# # Partial functions pour paths et timedeltas
# static_path = partial(Path.joinpath, BASE_DIR)
# media_path = partial(Path.joinpath, BASE_DIR)
# jwt_timedelta = partial(timedelta)

# # SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = env('SECRET_KEY')

# # SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = env.bool('DEBUG', default=False)

# ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# # Application definition
# INSTALLED_APPS = [
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',

#     # Third party apps
#     'corsheaders',
#     'rest_framework',
#     'rest_framework_simplejwt',  # ← Ajouté pour JWT
#     'django_filters',
#     'anymail',
#     'django_celery_beat',
#     'django_celery_results',
    
#     # Local apps
#     'apps.utilisateur',
#     'apps.products',
#     'apps.orders',
#     'apps.marketplace',
#     'apps.dashboard',
# ]

# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',
#     'corsheaders.middleware.CorsMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
#     'django_htmx.middleware.HtmxMiddleware',
# ]

# ROOT_URLCONF = 'config.urls'

# # Custom user model (de notre UML : Utilisateur avec rôles Client/Entreprise)
# AUTH_USER_MODEL = 'utilisateur.Utilisateur'
# LOGIN_REDIRECT_URL = '/dashboard/index'  # Après login
# LOGOUT_REDIRECT_URL = 'marketplace/home/'  # Après logout
# LOGIN_URL = '/login/' # cette route 

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',  # ← Corrigé : DjangoTemplates
#         'DIRS': [BASE_DIR / 'templates'],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#                 'config.context_processors.unread_notifications',
#                 'apps.orders.context_processors.cart_context',
#                 "marketplace.context_processors.cart_context",
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = 'config.wsgi.application'

# # Database (PostgreSQL avec options avancées)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': env('DB_NAME'),
#         'USER': env('DB_USER'),
#         'PASSWORD': env('DB_PASSWORD'),
#         'HOST': env('DB_HOST', default='localhost'),
#         'PORT': env('DB_PORT', default='5432'),
#         'OPTIONS': {
#             'connect_timeout': 10,
#             'sslmode': 'require' if env.bool('DB_SSL', default=False) else 'disable',
#         },
#         'CONN_MAX_AGE': env.int('DB_CONN_MAX_AGE', default=0),
#         'CONN_HEALTH_CHECKS': True,  # Django 6.0 OK
#     }
# }

# # Password validation
# AUTH_PASSWORD_VALIDATORS = [
#     {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
# ]

# # Internationalization (fr-fr pour agro FR, avec formats €/dates locales)
# LANGUAGE_CODE = 'fr-fr'
# TIME_ZONE = 'Europe/Paris'
# USE_I18N = True
# USE_TZ = True
# USE_L10N = True

# # Static files
# STATIC_URL = '/static/'
# STATIC_ROOT = static_path('staticfiles')
# STATICFILES_DIRS = [
#     APPS_DIR / "marketplace" / "static",
#     APPS_DIR / "dashboard" / "static",
# ]

# MEDIA_URL = '/media/'
# MEDIA_ROOT = media_path('media')
# DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'  # Fallback local

# # REST Framework (avec search/ordering pour catalogue produits agro)
# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': (
#         'rest_framework_simplejwt.authentication.JWTAuthentication',
#     ),
#     'DEFAULT_PERMISSION_CLASSES': (
#         'rest_framework.permissions.IsAuthenticatedOrReadOnly',
#     ),
#     'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
#     'PAGE_SIZE': env.int('API_PAGE_SIZE', default=20),
#     'DEFAULT_FILTER_BACKENDS': [
#         'django_filters.rest_framework.DjangoFilterBackend',
#         'rest_framework.filters.SearchFilter',  # Ex: search "tomates bio"
#         'rest_framework.filters.OrderingFilter',
#     ],
# }

# # JWT
# SIMPLE_JWT = {
#     'ACCESS_TOKEN_LIFETIME': jwt_timedelta(hours=1),
#     'REFRESH_TOKEN_LIFETIME': jwt_timedelta(days=7),
#     'ROTATE_REFRESH_TOKENS': True,
#     'BLACKLIST_AFTER_ROTATION': True,
# }
# # cet module est utilisé pour planifier des tâches périodiques avec Celery et Django
# from celery.schedules import crontab

# # Celery (broker Redis, tâche low-stock pour Products)
# CELERY_BROKER_URL = env('CELERY_BROKER', default='redis://localhost:6379/0')
# CELERY_RESULT_BACKEND = env('CELERY_BACKEND', default='redis://localhost:6379/0')
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TIMEZONE = TIME_ZONE
# CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
# CELERY_BEAT_SCHEDULE = {
#     'check-low-stock-every-hour': {
#         'task': 'apps.products.tasks.check_low_stock',  
#         'schedule': jwt_timedelta(hours=1).total_seconds(),
#         'daily-producer-report': {
#         'task': 'tasks.email_tasks.send_daily_producer_report',
#         'schedule': crontab(hour=6, minute=0),
#     },
#     'reset-daily-stats': {
#         'task': 'tasks.product_tasks.update_product_statistics',
#         'schedule': crontab(hour=0, minute=0),
#     },
#     },
# }
# # Security settings (relâchés pour dev local)
# CSRF_COOKIE_SECURE = False  # Pour HTTP local (pas HTTPS)
# CSRF_COOKIE_HTTPONLY = False  # Permet JS access (si tu gardes le script)
# CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8000', 'http://localhost:8000']  # 


# # Email (Anymail/SendGrid par défaut)
# EMAIL_BACKEND = 'anymail.backends.sendgrid.EmailBackend' 
# ANYMAIL = {
#     "SENDGRID_API_KEY": env('SENDGRID_KEY', default=''),
# }
# DEFAULT_FROM_EMAIL = env('DEFAULT_EMAIL', default='noreply@agrimarket.com')
# SERVER_EMAIL = DEFAULT_FROM_EMAIL

# # Email backend pour dev (affiche mails dans console)
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Change en 'smtp' ou Anymail pour prod
# DEFAULT_FROM_EMAIL = 'noreply@agribusiness.com'  # Expéditeur des mails reset

# # Pour prod (ex: SendGrid, comme dans ton Anymail config)
# # EMAIL_BACKEND = 'anymail.backends.sendgrid.EmailBackend'
# # ANYMAIL = {"SENDGRID_API_KEY": env('SENDGRID_KEY')}
# # EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# # EMAIL_HOST = 'smtp.gmail.com'
# # EMAIL_PORT = 587
# # EMAIL_USE_TLS = True
# # EMAIL_HOST_USER = 'tonemail@gmail.com'
# # EMAIL_HOST_PASSWORD = 'tonpassapp'
# # DEFAULT_FROM_EMAIL = 'noreply@agrobusiness.com'

# # URLs pour reset (optionnel, mais utile)
# PASSWORD_RESET_TIMEOUT = 259200  # 3 jours en secondes

# #Payment
# # settings.py
# STRIPE_PUBLIC_KEY = env('STRIPE_PUBLISHABLE_KEY', default='')
# STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')