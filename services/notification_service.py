# services/notification_service.py

import logging
from django.contrib.auth import get_user_model
from apps.utilisateur.models import Notification 
from apps.orders.models import Order
from apps.products.models import Product
from .email_service import AsyncEmailService

logger = logging.getLogger(__name__)

User = get_user_model()

class NotificationService:
    """Service centralisé pour les notifications in-app et email"""

    NOTIFICATION_TYPES = {
        'NEW_ORDER': 'Nouvelle commande',
        'LOW_STOCK': 'Stock bas',
        'ORDER_UPDATE': 'Mise à jour commande',
        'MESSAGE': 'Nouveau message',
        'INFO': 'Information générale',
        'PAYMENT_SUCCESS': 'Paiement confirmé',
        'PAYMENT_FAILED': 'Paiement échoué',
    }

    @staticmethod
    def create_in_app_notification(
        user,
        type_notif: str,
        title: str,
        message: str,
        order: Order = None,
        product: Product = None,
    ):
        """Crée une notification in-app en base de données"""
        try:
            notification = Notification.objects.create(
                user=user,
                type=type_notif,
                title=title,
                message=message,
                related_order=order,
                related_product=product,
            )
            logger.info(f"Notification in-app créée pour {user.username} : {title}")
            return notification
        except Exception as e:
            logger.error(f"Erreur création notification in-app pour {user.username} : {e}")
            return None

    @staticmethod
    def notify_new_order(order: Order):
        """Notifie tous les producteurs concernés par une nouvelle commande"""
        if not order.items.exists():
            return

        # Récupérer les producteurs uniques
        producers = {
            item.product.producer.user for item in order.items.all()
            if hasattr(item.product, 'producer') and item.product.producer
        }

        for producer in producers:
            # Notification in-app
            NotificationService.create_in_app_notification(
                user=producer,
                type_notif='NEW_ORDER',
                title=f"Nouvelle commande #{order.order_number}",
                message=f"Un client a commandé vos produits pour un total de {order.total_amount}€.",
                order=order,
            )

            # Email async au producteur
            AsyncEmailService.send_new_order_alert(order)

        logger.info(f"Notifications nouvelle commande #{order.order_number} envoyées à {len(producers)} producteur(s)")

    @staticmethod
    def notify_low_stock(product: Product, threshold: int = 10):
        """Notifie le producteur si stock bas"""
        if not product.producer or product.stock > threshold:
            return

        producer_user = product.producer.user

        # Notification in-app
        NotificationService.create_in_app_notification(
            user=producer_user,
            type_notif='LOW_STOCK',
            title=f"Stock faible : {product.name}",
            message=f"Il reste seulement {product.stock} unité(s) en stock. Réapprovisionnez-vous rapidement !",
            product=product,
        )

        # Email async
        AsyncEmailService.send_low_stock_alert(product.producer, [product])

        logger.warning(f"Alerte stock bas envoyée pour {product.name} (stock: {product.stock}) à {producer_user.username}")

    @staticmethod
    def notify_multiple_low_stock(products: list, threshold: int = 10):
        """Version optimisée pour plusieurs produits (ex: tâche quotidienne)"""
        if not products:
            return

        # Grouper par producteur
        from collections import defaultdict
        producer_products = defaultdict(list)

        for product in products:
            if product.producer:
                producer_products[product.producer.user].append(product)

        for producer_user, prod_list in producer_products.items():
            # Notification in-app groupée
            NotificationService.create_in_app_notification(
                user=producer_user,
                type_notif='LOW_STOCK',
                title=f"Alertes stock bas ({len(prod_list)} produits)",
                message=f"Plusieurs de vos produits ont un stock faible. Vérifiez votre inventaire.",
            )

            # Email groupé
            AsyncEmailService.send_low_stock_alert(producer_user.producer_profile, prod_list)

        logger.info(f"Alertes stock bas groupées envoyées à {len(producer_products)} producteur(s)")

    @staticmethod
    def notify_order_update(order: Order, update_type: str = "status"):
        """Notifie le client d'une mise à jour de commande"""
        NotificationService.create_in_app_notification(
            user=order.client,
            type_notif='ORDER_UPDATE',
            title=f"Votre commande #{order.order_number} a été mise à jour",
            message=f"Le statut de votre commande a changé. Consultez les détails.",
            order=order,
        )

        # Optionnel : email aussi
        # AsyncEmailService.send_order_update_email(order)

    @staticmethod
    def notify_payment_success(order: Order):
        """Notifie le client du succès du paiement"""
        NotificationService.create_in_app_notification(
            user=order.client,
            type_notif='PAYMENT_SUCCESS',
            title=f"Paiement confirmé pour la commande #{order.order_number}",
            message=f"Votre paiement de {order.total_amount}€ a été accepté. Merci !",
            order=order,
        )

    @staticmethod
    def notify_payment_failed(order: Order, reason: str = ""):
        """Notifie le client d'un échec de paiement"""
        message = "Votre paiement a échoué."
        if reason:
            message += f" Raison : {reason}"

        NotificationService.create_in_app_notification(
            user=order.client,
            type_notif='PAYMENT_FAILED',
            title=f"Échec paiement commande #{order.order_number}",
            message=message,
            order=order,
        )