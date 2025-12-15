from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

logger = get_task_logger(__name__)

@shared_task(bind=True, max_retries=3, retry_backoff=True)
def send_order_confirmation_task(self, order_id):
    """Envoie la confirmation de commande"""
    from apps.orders.models import Order
    
    try:
        order = Order.objects.get(id=order_id)
        html_message = render_to_string('emails/order_confirmation.html', {
            'order': order,
            'items': order.items.all(),
            'total': order.total_amount,
        })
        
        send_mail(
            subject=f'Commande #{order.order_number} confirmée',
            message='Votre commande a été confirmée.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.client.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email confirmation envoyé pour commande #{order.order_number}")
        return f"Email sent to {order.client.email}"
        
    except Order.DoesNotExist:
        logger.error(f"Commande {order_id} introuvable")
        return "Order not found"
    
    except Exception as e:
        logger.error(f"Erreur envoi email: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, rate_limit='10/m')
def send_bulk_notification_task(self, user_ids, subject, message):
    """Envoie des emails en masse avec rate limiting"""
    from apps.utilisateur.models import utilisateur
    
    users = utilisateur.objects.filter(id__in=user_ids)
    sent = 0
    
    for user in users:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            sent += 1
        except Exception as e:
            logger.error(f"Erreur envoi à {user.email}: {e}")
    
    logger.info(f"{sent}/{users.count()} emails envoyés")
    return f"{sent}/{users.count()} emails sent"


@shared_task
def send_daily_producer_report():
    """Rapport quotidien pour les producteurs"""
    from apps.utilisateur.models import utilisateur
    from apps.orders.models import Order
    from django.utils import timezone
    
    producers = utilisateur.objects.filter(role='PRODUCTEUR')
    today = timezone.now().date()
    
    for producer in producers:
        orders = Order.objects.filter(
            items__product__producer__user=producer,
            created_at__date=today
        ).distinct()
        
        total = sum(o.total_amount for o in orders)
        
        send_mail(
            subject=f"Votre rapport du {today}",
            message=f"Vous avez reçu {orders.count()} commandes pour un total de {total}€",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[producer.email],
        )
    
    logger.info(f"Rapports envoyés à {producers.count()} producteurs")
    return f"Reports sent to {producers.count} producers"


# from celery import shared_task
# from celery.utils.log import get_task_logger
# from django.core.mail import send_mail
# from apps.orders.models import Order
# from apps.products.models import Product

# logger = get_task_logger(__name__)

# @shared_task(bind=True, max_retries=3, default_retry_delay=60)
# def send_order_confirmation_task(self, order_id: int):
#     """Tâche async pour confirmation de commande"""
#     try:
#         order = Order.objects.get(id=order_id)
#         subject = f"Commande #{order.order_number} confirmée"
#         message = f"""
#         Bonjour {order.client.username},
        
#         Votre commande a été confirmée.
#         Total: {order.total_amount}€
        
#         Merci de votre confiance !
#         """
        
#         send_mail(
#             subject,
#             message,
#             'orders@agrimarket.com',
#             [order.client.email],
#             fail_silently=False,
#         )
#         logger.info(f"Confirmation envoyée pour commande #{order.order_number}")
#         return f"Email sent to {order.client.email}"
    
#     except Order.DoesNotExist:
#         logger.error(f"Commande {order_id} introuvable")
#         return "Order not found"
    
#     except Exception as e:
#         logger.error(f"Erreur email: {e}")
#         raise self.retry(exc=e)

# @shared_task
# def send_daily_producer_report():
#     """Rapport quotidien pour les producteurs"""
#     from apps.users.models import User
#     from django.utils import timezone
    
#     producers = User.objects.filter(role='PRODUCTEUR')
#     today = timezone.now().date()
    
#     for producer in producers:
#         orders = Order.objects.filter(
#             items__product__producer__user=producer,
#             created_at__date=today
#         ).distinct()
        
#         total = sum(order.total_amount for order in orders)
        
#         send_mail(
#             f"Votre rapport du {today}",
#             f"Vous avez reçu {orders.count()} commandes pour un total de {total}€",
#             'reports@agrimarket.com',
#             [producer.email],
#         )
    
#     return f"Rapports envoyés à {producers.count()} producteurs"

# @shared_task(bind=True, rate_limit='10/m')
# def send_bulk_notification(self, user_ids, subject, message):
#     """Envoi massif de emails avec rate limiting"""
#     from django.contrib.auth import get_user_model
#     User = get_user_model()
    
#     users = User.objects.filter(id__in=user_ids)
#     sent = 0
    
#     for user in users:
#         try:
#             send_mail(subject, message, 'noreply@agrimarket.com', [user.email])
#             sent += 1
#         except Exception as e:
#             logger.error(f"Erreur envoi à {user.email}: {e}")
    
#     return f"{sent}/{users.count()} emails envoyés"