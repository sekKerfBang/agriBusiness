import logging
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model

from apps.utilisateur.models import Notification
from apps.orders.models import Order
from apps.products.models import Product
from .email_service import EmailService

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationService:
    """Service centralisé de notifications in-app et emails"""
    
    # Types de notifications
    NOTIFICATION_TYPES = {
        'INFO': 'information',
        'WARNING': 'avertissement',
        'SUCCESS': 'succès',
        'ERROR': 'erreur',
        'ORDER': 'commande',
        'STOCK': 'stock',
        'PAYMENT': 'paiement',
        'SYSTEM': 'système',
    }
    
    @staticmethod
    def create_notification(
        user_id: int,
        title: str,
        message: str,
        notification_type: str = 'INFO',
        related_order_id: Optional[int] = None,
        related_product_id: Optional[int] = None,
        priority: int = 1,  # 1: bas, 2: moyen, 3: élevé
        expires_at: Optional[timezone.datetime] = None
    ) -> Optional[Notification]:
        """
        Crée une notification in-app
        """
        try:
            with transaction.atomic():
                notification = Notification.objects.create(
                    user_id=user_id,
                    title=title,
                    message=message,
                    type=notification_type,
                    priority=priority,
                    related_order_id=related_order_id,
                    related_product_id=related_product_id,
                    expires_at=expires_at or (timezone.now() + timezone.timedelta(days=30))
                )
                
                # Mettre à jour le cache du nombre de notifications non lues
                cache_key = f"unread_notifications_{user_id}"
                cache.delete(cache_key)
                
                logger.info(f"📨 Notification créée pour user {user_id} : {title}")
                return notification
                
        except Exception as e:
            logger.error(f"❌ Erreur création notification user {user_id} : {e}")
            return None
    
    @staticmethod
    def get_unread_count(user_id: int) -> int:
        """
        Récupère le nombre de notifications non lues (avec cache)
        """
        cache_key = f"unread_notifications_{user_id}"
        count = cache.get(cache_key)
        
        if count is None:
            count = Notification.objects.filter(
                user_id=user_id,
                is_read=False,
                expires_at__gte=timezone.now()
            ).count()
            cache.set(cache_key, count, timeout=300)  # Cache 5 minutes
        
        return count
    
    @staticmethod
    def mark_as_read(notification_id: int, user_id: int) -> bool:
        """
        Marque une notification comme lue
        """
        try:
            updated = Notification.objects.filter(
                id=notification_id,
                user_id=user_id,
                is_read=False
            ).update(
                is_read=True,
                read_at=timezone.now()
            )
            
            if updated:
                # Mettre à jour le cache
                cache_key = f"unread_notifications_{user_id}"
                cache.delete(cache_key)
                logger.debug(f"Notification {notification_id} marquée comme lue")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erreur marquer notification lue {notification_id} : {e}")
            return False
    
    @staticmethod
    def mark_all_as_read(user_id: int) -> int:
        """
        Marque toutes les notifications comme lues
        """
        try:
            count = Notification.objects.filter(
                user_id=user_id,
                is_read=False,
                expires_at__gte=timezone.now()
            ).update(
                is_read=True,
                read_at=timezone.now()
            )
            
            # Mettre à jour le cache
            cache_key = f"unread_notifications_{user_id}"
            cache.delete(cache_key)
            
            logger.info(f"📭 {count} notifications marquées comme lues pour user {user_id}")
            return count
            
        except Exception as e:
            logger.error(f"Erreur marquer toutes notifications lues user {user_id} : {e}")
            return 0
    
    @staticmethod
    def clean_old_notifications(days_old: int = 90) -> int:
        """
        Nettoie les notifications expirées
        """
        try:
            cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
            deleted_count, _ = Notification.objects.filter(
                created_at__lt=cutoff_date
            ).delete()
            
            logger.info(f"🧹 {deleted_count} anciennes notifications nettoyées")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Erreur nettoyage notifications : {e}")
            return 0
    
    # Méthodes métier
    @classmethod
    def notify_new_order(cls, order: Order) -> Dict[str, Any]:
        """
        Notifie les producteurs d'une nouvelle commande
        Retourne le nombre de notifications créées
        """
        if not order.items.exists():
            return {'notifications': 0, 'emails': 0}
        
        notifications_created = 0
        emails_sent = 0
        
        # Grouper par producteur
        producers_dict = {}
        for item in order.items.all():
            if hasattr(item.product, 'producer') and item.product.producer:
                producer_user = item.product.producer.user
                if producer_user.id not in producers_dict:
                    producers_dict[producer_user.id] = {
                        'user': producer_user,
                        'products': [],
                        'total_amount': 0
                    }
                producers_dict[producer_user.id]['products'].append(item.product)
                producers_dict[producer_user.id]['total_amount'] += item.quantity * item.unit_price
        
        # Créer les notifications et envoyer les emails
        for producer_data in producers_dict.values():
            producer_user = producer_data['user']
            products = producer_data['products']
            total = producer_data['total_amount']
            
            # Notification in-app
            notification = cls.create_notification(
                user_id=producer_user.id,
                title=f"📦 Nouvelle commande #{order.order_number}",
                message=f"Vous avez reçu une nouvelle commande pour {len(products)} produit(s). Montant : {total:.2f}€",
                notification_type='ORDER',
                related_order_id=order.id,
                priority=2
            )
            
            if notification:
                notifications_created += 1
            
            # Email au producteur
            email_sent = EmailService.send_template_email(
                recipient_email=producer_user.email,
                subject=f"📦 Nouvelle commande #{order.order_number}",
                template_name='new_order_producer',
                context={
                    'producer': producer_user,
                    'order': order,
                    'products': products,
                    'total_amount': total,
                    'order_date': order.created_at
                }
            )
            
            if email_sent:
                emails_sent += 1
        
        # Notification au client
        cls.create_notification(
            user_id=order.client.id,
            title=f"✅ Commande #{order.order_number} confirmée",
            message=f"Votre commande a été confirmée. Montant total : {order.total_amount:.2f}€",
            notification_type='ORDER',
            related_order_id=order.id,
            priority=1
        )
        
        logger.info(f"📦 Commande #{order.order_number} : {notifications_created} notifications, {emails_sent} emails")
        return {
            'notifications': notifications_created,
            'emails': emails_sent,
            'producers': len(producers_dict)
        }
    
    @classmethod
    def notify_low_stock(cls, product: Product, threshold: int = 10) -> bool:
        """
        Notifie le producteur d'un stock bas
        """
        if not product.producer or product.stock > threshold:
            return False
        
        # Vérifier si déjà notifié aujourd'hui
        cache_key = f"low_stock_notified_{product.id}_{timezone.now().date()}"
        if cache.get(cache_key):
            logger.debug(f"Stock bas déjà notifié aujourd'hui pour {product.name}")
            return False
        
        producer_user = product.producer.user
        
        # Notification in-app
        notification = cls.create_notification(
            user_id=producer_user.id,
            title=f"⚠️ Stock faible : {product.name}",
            message=f"Il reste seulement {product.stock} unité(s) en stock. Seuil d'alerte : {threshold}",
            notification_type='STOCK',
            related_product_id=product.id,
            priority=2
        )
        
        # Email
        email_sent = EmailService.send_low_stock_alert(
            producer=product.producer,
            products=[product]
        )
        
        if notification or email_sent:
            # Mettre en cache pour 24h
            cache.set(cache_key, True, timeout=86400)
            logger.warning(f"⚠️ Alerte stock bas : {product.name} (stock: {product.stock})")
            return True
        
        return False
    
    @classmethod
    def notify_order_status_update(cls, order: Order, old_status: str, new_status: str) -> bool:
        """
        Notifie le client d'un changement de statut
        """
        status_messages = {
            'PROCESSING': 'en cours de traitement',
            'SHIPPED': 'expédiée',
            'DELIVERED': 'livrée',
            'CANCELLED': 'annulée'
        }
        
        message = f"Votre commande est maintenant {status_messages.get(new_status, new_status.lower())}."
        if old_status:
            message = f"Statut changé de {old_status} à {new_status.lower()}. {message}"
        
        # Notification in-app
        notification = cls.create_notification(
            user_id=order.client.id,
            title=f"🔄 Commande #{order.order_number} mise à jour",
            message=message,
            notification_type='ORDER',
            related_order_id=order.id,
            priority=1
        )
        
        # Email si statut important
        if new_status in ['SHIPPED', 'DELIVERED', 'CANCELLED']:
            EmailService.send_template_email(
                recipient_email=order.client.email,
                subject=f"🔄 Mise à jour commande #{order.order_number}",
                template_name='order_status_update',
                context={
                    'order': order,
                    'old_status': old_status,
                    'new_status': new_status,
                    'status_message': status_messages.get(new_status, '')
                }
            )
        
        return notification is not None
    
    @classmethod
    def notify_payment_success(cls, order: Order) -> bool:
        """
        Notifie le client d'un paiement réussi
        """
        # Notification in-app
        notification = cls.create_notification(
            user_id=order.client.id,
            title=f"✅ Paiement confirmé #{order.order_number}",
            message=f"Votre paiement de {order.total_amount:.2f}€ a été accepté. Merci !",
            notification_type='PAYMENT',
            related_order_id=order.id,
            priority=1
        )
        
        return notification is not None
    
    @classmethod
    def notify_system_alert(cls, users: List[User], title: str, message: str) -> int:
        """
        Notifie plusieurs utilisateurs d'une alerte système
        """
        notifications_created = 0
        
        for user in users:
            notification = cls.create_notification(
                user_id=user.id,
                title=f"🔔 {title}",
                message=message,
                notification_type='SYSTEM',
                priority=3  # Haute priorité
            )
            
            if notification:
                notifications_created += 1
        
        logger.info(f"🔔 Alerte système envoyée à {notifications_created}/{len(users)} utilisateurs")
        return notifications_created





# # services/notification_service.py

# import logging
# from django.contrib.auth import get_user_model
# from apps.utilisateur.models import Notification 
# from apps.orders.models import Order
# from apps.products.models import Product
# from .email_service import AsyncEmailService

# logger = logging.getLogger(__name__)

# User = get_user_model()

# class NotificationService:
#     """Service centralisé pour les notifications in-app et email"""

#     NOTIFICATION_TYPES = {
#         'NEW_ORDER': 'Nouvelle commande',
#         'LOW_STOCK': 'Stock bas',
#         'ORDER_UPDATE': 'Mise à jour commande',
#         'MESSAGE': 'Nouveau message',
#         'INFO': 'Information générale',
#         'PAYMENT_SUCCESS': 'Paiement confirmé',
#         'PAYMENT_FAILED': 'Paiement échoué',
#     }

#     @staticmethod
#     def create_in_app_notification(
#         user,
#         type_notif: str,
#         title: str,
#         message: str,
#         order: Order = None,
#         product: Product = None,
#     ):
#         """Crée une notification in-app en base de données"""
#         try:
#             notification = Notification.objects.create(
#                 user=user,
#                 type=type_notif,
#                 title=title,
#                 message=message,
#                 related_order=order,
#                 related_product=product,
#             )
#             logger.info(f"Notification in-app créée pour {user.username} : {title}")
#             return notification
#         except Exception as e:
#             logger.error(f"Erreur création notification in-app pour {user.username} : {e}")
#             return None

#     @staticmethod
#     def notify_new_order(order: Order):
#         """Notifie tous les producteurs concernés par une nouvelle commande"""
#         if not order.items.exists():
#             return

#         # Récupérer les producteurs uniques
#         producers = {
#             item.product.producer.user for item in order.items.all()
#             if hasattr(item.product, 'producer') and item.product.producer
#         }

#         for producer in producers:
#             # Notification in-app
#             NotificationService.create_in_app_notification(
#                 user=producer,
#                 type_notif='NEW_ORDER',
#                 title=f"Nouvelle commande #{order.order_number}",
#                 message=f"Un client a commandé vos produits pour un total de {order.total_amount}€.",
#                 order=order,
#             )

#             # Email async au producteur
#             AsyncEmailService.send_new_order_alert(order)

#         logger.info(f"Notifications nouvelle commande #{order.order_number} envoyées à {len(producers)} producteur(s)")

#     @staticmethod
#     def notify_low_stock(product: Product, threshold: int = 10):
#         """Notifie le producteur si stock bas"""
#         if not product.producer or product.stock > threshold:
#             return

#         producer_user = product.producer.user

#         # Notification in-app
#         NotificationService.create_in_app_notification(
#             user=producer_user,
#             type_notif='LOW_STOCK',
#             title=f"Stock faible : {product.name}",
#             message=f"Il reste seulement {product.stock} unité(s) en stock. Réapprovisionnez-vous rapidement !",
#             product=product,
#         )

#         # Email async
#         AsyncEmailService.send_low_stock_alert(product.producer, [product])

#         logger.warning(f"Alerte stock bas envoyée pour {product.name} (stock: {product.stock}) à {producer_user.username}")

#     @staticmethod
#     def notify_multiple_low_stock(products: list, threshold: int = 10):
#         """Version optimisée pour plusieurs produits (ex: tâche quotidienne)"""
#         if not products:
#             return

#         # Grouper par producteur
#         from collections import defaultdict
#         producer_products = defaultdict(list)

#         for product in products:
#             if product.producer:
#                 producer_products[product.producer.user].append(product)

#         for producer_user, prod_list in producer_products.items():
#             # Notification in-app groupée
#             NotificationService.create_in_app_notification(
#                 user=producer_user,
#                 type_notif='LOW_STOCK',
#                 title=f"Alertes stock bas ({len(prod_list)} produits)",
#                 message=f"Plusieurs de vos produits ont un stock faible. Vérifiez votre inventaire.",
#             )

#             # Email groupé
#             AsyncEmailService.send_low_stock_alert(producer_user.producer_profile, prod_list)

#         logger.info(f"Alertes stock bas groupées envoyées à {len(producer_products)} producteur(s)")

#     @staticmethod
#     def notify_order_update(order: Order, update_type: str = "status"):
#         """Notifie le client d'une mise à jour de commande"""
#         NotificationService.create_in_app_notification(
#             user=order.client,
#             type_notif='ORDER_UPDATE',
#             title=f"Votre commande #{order.order_number} a été mise à jour",
#             message=f"Le statut de votre commande a changé. Consultez les détails.",
#             order=order,
#         )

#         # Optionnel : email aussi
#         # AsyncEmailService.send_order_update_email(order)

#     @staticmethod
#     def notify_payment_success(order: Order):
#         """Notifie le client du succès du paiement"""
#         NotificationService.create_in_app_notification(
#             user=order.client,
#             type_notif='PAYMENT_SUCCESS',
#             title=f"Paiement confirmé pour la commande #{order.order_number}",
#             message=f"Votre paiement de {order.total_amount}€ a été accepté. Merci !",
#             order=order,
#         )

#     @staticmethod
#     def notify_payment_failed(order: Order, reason: str = ""):
#         """Notifie le client d'un échec de paiement"""
#         message = "Votre paiement a échoué."
#         if reason:
#             message += f" Raison : {reason}"

#         NotificationService.create_in_app_notification(
#             user=order.client,
#             type_notif='PAYMENT_FAILED',
#             title=f"Échec paiement commande #{order.order_number}",
#             message=message,
#             order=order,
#         )