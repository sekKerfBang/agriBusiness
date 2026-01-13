from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from django_celery_results.models import TaskResult
from django.core.cache import cache

logger = get_task_logger(__name__)


@shared_task
def cleanup_old_tasks():
    """
    Nettoie les anciennes tâches et les résultats
    """
    try:
        # Supprimer les résultats de tâches de plus de 7 jours
        cutoff_date = timezone.now() - timedelta(days=7)
        deleted_count, _ = TaskResult.objects.filter(
            date_done__lt=cutoff_date
        ).delete()
        
        logger.info(f"🧹 {deleted_count} anciens résultats de tâches nettoyés")
        
        # Nettoyer le cache des tâches
        cache.delete_pattern('task:*')
        
        return {
            'deleted_tasks': deleted_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur nettoyage tâches : {e}")
        return {'error': str(e)}


@shared_task
def monitor_system_health():
    """
    Surveille la santé du système et envoie des alertes
    """
    try:
        from django.db import connection
        from apps.utilisateur.models import Utilisateur
        from apps.orders.models import Order
        from apps.products.models import Product
        
        health_status = {
            'timestamp': timezone.now().isoformat(),
            'database': 'OK',
            'users_count': Utilisateur.objects.count(),
            'active_users': Utilisateur.objects.filter(is_active=True).count(),
            'orders_today': Order.objects.filter(
                created_at__date=timezone.now().date()
            ).count(),
            'low_stock_products': Product.objects.filter(
                stock__lte=10, is_active=True
            ).count(),
        }
        
        # Vérifier la connexion DB
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status['database'] = 'OK'
        except Exception as e:
            health_status['database'] = f'ERROR: {e}'
            logger.error(f"❌ Problème de base de données : {e}")
        
        # Log du statut
        logger.info(f"🩺 Santé système : {health_status}")
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Erreur monitoring santé : {e}")
        return {'error': str(e)}


@shared_task
def backup_database():
    """
    Sauvegarde de la base de données (à adapter selon votre configuration)
    """
    try:
        import subprocess
        from django.conf import settings
        import os
        
        # Chemin de sauvegarde
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Nom du fichier avec timestamp
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.sql')
        
        # Commande de sauvegarde PostgreSQL (à adapter)
        db = settings.DATABASES['default']
        command = [
            'pg_dump',
            '-h', db['HOST'],
            '-U', db['USER'],
            '-d', db['NAME'],
            '-f', backup_file
        ]
        
        # Exécuter avec mot de passe dans l'environnement
        env = os.environ.copy()
        env['PGPASSWORD'] = db['PASSWORD']
        
        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Compresser le backup
            import gzip
            with open(backup_file, 'rb') as f_in:
                with gzip.open(f"{backup_file}.gz", 'wb') as f_out:
                    f_out.writelines(f_in)
            
            # Supprimer le fichier non compressé
            os.remove(backup_file)
            
            # Garder seulement les 7 derniers backups
            backups = sorted([
                f for f in os.listdir(backup_dir)
                if f.endswith('.gz')
            ], reverse=True)
            
            for old_backup in backups[7:]:
                os.remove(os.path.join(backup_dir, old_backup))
            
            logger.info(f"💾 Sauvegarde DB réussie : {backup_file}.gz")
            return {'success': True, 'backup_file': f"{backup_file}.gz"}
        else:
            logger.error(f"❌ Échec sauvegarde DB : {result.stderr}")
            return {'success': False, 'error': result.stderr}
            
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde DB : {e}")
        return {'success': False, 'error': str(e)}