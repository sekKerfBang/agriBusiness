import logging
from typing import Dict, Any
from datetime import datetime
from functools import partial
from apps.utilisateur.models import utilisateur

logger = logging.getLogger(__name__)

# Partial pour créer des notif types rapidement
create_notification = partial(dict, timestamp=datetime.now().isoformat())

class NotificationService:
    """Centralise toutes les notifications (push, email, in-app)"""
    
    @staticmethod
    def notify_new_order(order: Any):
        """Notifie le producteur d'une nouvelle commande"""
        producer = order.items.first().product.producer.user
        
        # Notification in-app
        notification = create_notification(
            type='NEW_ORDER',
            title=f"Nouvelle commande #{order.order_number}",
            message=f"Montant: {order.total_amount}€",
            recipient=producer.email,
            order_id=order.id
        )
        
        # Email async
        from services.email_service import AsyncEmailService
        AsyncEmailService.send_new_order_alert(order)
        
        # Push notification (Firebase à implémenter)
        # FirebaseService.send_push(producer.device_token, notification)
        
        logger.info(f"Notification envoyée pour commande {order.order_number}")
    
    @staticmethod
    def notify_low_stock(product: Any, threshold: int = 10):
        """Alerte stock bas"""
        if product.stock < threshold:
            producer = product.producer.user
            
            notification = create_notification(
                type='LOW_STOCK',
                title=f"Stock bas: {product.name}",
                message=f"Il reste {product.stock} {product.unit}",
                product_id=product.id
            )
            
            # Email async
            from services.email_service import send_low_stock_alert
            send_low_stock_alert(
                to=producer.email,
                context={'product': product, 'threshold': threshold}
            )
            
            logger.warning(f"Alerte stock bas: {product.name} ({product.stock})")