# tasks/notification_tasks.py

import logging
from typing import List, Dict, Any
from config.celery_app import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.core.cache import cache

from apps.utilisateur.models import Utilisateur, Notification
from apps.orders.models import Order
from apps.products.models import Product
from services.notification_service import NotificationService

logger = get_task_logger(__name__)

# cet decorateur permet de definir une tache asynchrone avec celery de maniere simple et reutilisable, et c'est natif a celery et django
@shared_task
def process_low_stock_alerts(threshold: int = 10) -> Dict[str, Any]:
    """
    Vérifie les produits en stock bas et envoie les alertes
    """
    try:
        # Récupérer les produits avec stock bas
        low_stock_products = Product.objects.filter(
            is_active=True,
            stock__gt=0,
            stock__lte=threshold,
            producer__isnull=False,
            producer__user__is_active=True
        ).select_related('producer__user')
        
        total_products = low_stock_products.count()
        alerts_sent = 0
        
        if total_products == 0:
            return {
                'alerts_sent': 0,
                'total_products': 0,
                'message': 'Aucun produit en stock bas'
            }
        
        # Grouper par producteur
        from collections import defaultdict
        producer_products = defaultdict(list)
        
        for product in low_stock_products:
            if product.producer:
                producer_products[product.producer.user].append(product)
        
        # Envoyer les alertes
        for producer_user, products in producer_products.items():
            try:
                # Notification groupée
                NotificationService.create_notification(
                    user_id=producer_user.id,
                    title=f"⚠️ Stock faible sur {len(products)} produit(s)",
                    message=f"{len(products)} de vos produits ont un stock inférieur à {threshold} unités.",
                    notification_type='STOCK',
                    priority=2
                )
                
                # Email groupé
                from services.email_service import EmailService
                EmailService.send_low_stock_alert(
                    producer=producer_user.producer_profile,
                    products=products
                )
                
                alerts_sent += 1
                
                # Mettre en cache pour éviter les doublons aujourd'hui
                for product in products:
                    cache_key = f"low_stock_processed_{product.id}_{timezone.now().date()}"
                    cache.set(cache_key, True, timeout=86400)
                    
            except Exception as e:
                logger.error(f"❌ Erreur alerte producteur {producer_user.id} : {e}")
        
        logger.warning(f"⚠️ Alertes stock bas : {alerts_sent} producteurs notifiés, {total_products} produits")
        
        return {
            'alerts_sent': alerts_sent,
            'total_products': total_products,
            'producers_notified': len(producer_products)
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur tâche alertes stock : {e}")
        return {
            'error': str(e),
            'alerts_sent': 0
        }


@shared_task
def cleanup_old_notifications(days_to_keep: int = 90) -> Dict[str, Any]:
    """
    Nettoie les anciennes notifications
    """
    try:
        deleted_count = NotificationService.clean_old_notifications(days_to_keep)
        
        logger.info(f"🧹 {deleted_count} anciennes notifications nettoyées")
        
        return {
            'deleted_count': deleted_count,
            'days_to_keep': days_to_keep,
            'cleaned_at': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur nettoyage notifications : {e}")
        return {
            'error': str(e),
            'deleted_count': 0
        }


@shared_task
def send_system_maintenance_notification(
    title: str,
    message: str,
    user_roles: List[str] = None,
    user_ids: List[int] = None
) -> Dict[str, Any]:
    """
    Envoie une notification système à des utilisateurs spécifiques
    """
    try:
        # Construire la queryset
        users_query = Utilisateur.objects.filter(is_active=True)
        
        if user_ids:
            users_query = users_query.filter(id__in=user_ids)
        
        if user_roles:
            users_query = users_query.filter(role__in=user_roles)
        
        users = list(users_query.only('id', 'username'))
        total_users = len(users)
        
        if total_users == 0:
            return {
                'notifications_sent': 0,
                'total_users': 0,
                'message': 'Aucun utilisateur ciblé'
            }
        
        # Envoyer les notifications
        notifications_sent = NotificationService.notify_system_alert(
            users=users,
            title=title,
            message=message
        )
        
        logger.info(f"🔔 Notification système envoyée à {notifications_sent}/{total_users} utilisateurs")
        
        return {
            'notifications_sent': notifications_sent,
            'total_users': total_users,
            'title': title,
            'sent_at': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur notification système : {e}")
        return {
            'error': str(e),
            'notifications_sent': 0
        }


@shared_task
def sync_unread_notifications_cache() -> Dict[str, Any]:
    """
    Synchronise le cache des notifications non lues
    """
    try:
        # Récupérer tous les utilisateurs actifs
        active_users = Utilisateur.objects.filter(
            is_active=True
        ).values_list('id', flat=True)
        
        cache_updates = 0
        
        for user_id in active_users:
            # Calculer le vrai nombre
            real_count = Notification.objects.filter(
                user_id=user_id,
                is_read=False,
                expires_at__gte=timezone.now()
            ).count()
            
            # Mettre à jour le cache
            cache_key = f"unread_notifications_{user_id}"
            cache.set(cache_key, real_count, timeout=86400)  # 24h
            cache_updates += 1
        
        logger.info(f"🔄 Cache notifications mis à jour pour {cache_updates} utilisateurs")
        
        return {
            'cache_updates': cache_updates,
            'total_users': len(active_users),
            'synced_at': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur sync cache notifications : {e}")
        return {
            'error': str(e),
            'cache_updates': 0
        }