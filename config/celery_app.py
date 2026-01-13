import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Définir le module Django par défaut
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

app = Celery(
    'AgroBusiness',
    broker='redis://localhost:6379/0',          # ← force ici dès la création
    backend='redis://localhost:6379/1',         # ← ou 'django-db' si tu préfères
)


# Configuration Celery à partir des settings Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découverte automatique des tâches dans toutes les applications
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS + ['tasks'])

# Configuration des tâches périodiques (Celery Beat)
app.conf.beat_schedule = {
    # Tâches quotidiennes (7h du matin)
    # cette ligne definit une tache periodique qui envoie un rapport de ventes quotidien a 7h du matin a travers de la file d'attente 'reports'
    'daily-sales-report': {
        'task': 'tasks.email_tasks.send_daily_sales_report',
        'schedule': crontab(hour=7, minute=0),
        'options': {'queue': 'reports'}
    },
    # cette ligne definit une tache periodique qui verifie les produits en stock bas a 9h du matin a travers de la file d'attente 'notifications'
    'check-low-stock-alerts': {
        'task': 'tasks.notification_tasks.process_low_stock_alerts',
        'schedule': crontab(hour=9, minute=0),
        'kwargs': {'threshold': 10},
        'options': {'queue': 'notifications'}
    },
    #cette ligne definit une tache periodique qui met a jour les statistiques des produits a minuit a travers de la file d'attente 'products'
    'update-product-statistics': {
        'task': 'tasks.product_tasks.check_and_update_product_statistics',
        'schedule': crontab(hour=0, minute=0),  # Minuit
        'options': {'queue': 'products'}
    },
    'welcome-new-users': {
        'task': 'tasks.email_tasks.send_welcome_emails_to_new_users',
        'schedule': crontab(hour=8, minute=30),
        'options': {'queue': 'emails'}
    },
    
    # Tâches hebdomadaires (Lundi 8h)
    'weekly-cleanup-notifications': {
        'task': 'tasks.notification_tasks.cleanup_old_notifications',
        'schedule': crontab(day_of_week=1, hour=8, minute=0),  # Lundi 8h
        'kwargs': {'days_to_keep': 90},
        'options': {'queue': 'maintenance'}
    },
    
    # Tâches horaires
    'sync-notifications-cache': {
        'task': 'tasks.notification_tasks.sync_unread_notifications_cache',
        'schedule': crontab(minute=0),  # Toutes les heures
        'options': {'queue': 'notifications'}
    },
    
    # Tâches mensuelles (1er du mois à 6h)
    'deactivate-out-of-stock-products': {
        'task': 'tasks.product_tasks.check_and_deactivate_out_of_stock_products',
        'schedule': crontab(day_of_month=1, hour=6, minute=0),
        'options': {'queue': 'products'}
    },
    
    # Nettoyage quotidien (2h du matin)
    'daily-maintenance': {
        'task': 'tasks.periodic_tasks.cleanup_old_tasks',
        'schedule': crontab(hour=2, minute=0),
        'options': {'queue': 'maintenance'}
    },
}

# Configuration des files d'attente
app.conf.task_routes = {
    # Haute priorité
    'tasks.email_tasks.send_order_confirmation_task': {'queue': 'high_priority'},
    'tasks.email_tasks.send_password_reset_task': {'queue': 'high_priority'},
    'tasks.notification_tasks.process_low_stock_alerts': {'queue': 'high_priority'},
    
    # Priorité moyenne
    'tasks.email_tasks.send_daily_sales_report': {'queue': 'reports'},
    'tasks.email_tasks.send_bulk_newsletter_task': {'queue': 'bulk_emails'},
    'tasks.notification_tasks.*': {'queue': 'notifications'},
    
    # Tâches lourdes
    'tasks.product_tasks.generate_product_catalog_pdf': {'queue': 'heavy_tasks'},
    'tasks.product_tasks.check_and_update_product_statistics': {'queue': 'heavy_tasks'},
    
    # Maintenance
    'tasks.periodic_tasks.*': {'queue': 'maintenance'},
    'tasks.notification_tasks.cleanup_old_notifications': {'queue': 'maintenance'},
}

# Configuration de la tolérance aux fautes
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True
app.conf.worker_prefetch_multiplier = 1  # Important pour les tâches longues
app.conf.worker_max_tasks_per_child = 100  # Recycler les workers après 100 tâches
app.conf.task_track_started = True
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']

@app.task(bind=True)
def debug_task(self):
    """Tâche de débogage"""
    print(f'Request: {self.request!r}')
    return {'status': 'debug', 'task_id': self.request.id}

