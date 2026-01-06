# tasks/email_tasks.py

from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from apps.orders.models import Order
from apps.utilisateur.models import Utilisateur

logger = get_task_logger(__name__)

@shared_task(bind=True, max_retries=5, retry_backoff=True)
def send_order_confirmation_task(self, order_id: int):
    """Envoie l'email de confirmation de commande au client"""
    try:
        order = Order.objects.select_related('client').prefetch_related('items__product').get(id=order_id)

        html_message = render_to_string('emails/order_confirmation.html', {
            'order': order,
            'items': order.items.all(),
            'total': order.total_amount,
        })

        send_mail(
            subject=f"Votre commande #{order.order_number} est confirmée !",
            message="Votre commande a été confirmée avec succès.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.client.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Email confirmation envoyé pour commande #{order.order_number}")
        return f"Confirmation envoyée à {order.client.email}"

    except Order.DoesNotExist:
        logger.error(f"Commande {order_id} introuvable")
        return "Commande introuvable"
    except Exception as e:
        logger.error(f"Erreur envoi email confirmation {order_id} : {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, rate_limit='20/m')
def send_bulk_notification_task(self, user_ids: list, subject: str, message: str):
    """Envoi d'emails en masse (newsletter, promo, etc.)"""
    users = Utilisateur.objects.filter(id__in=user_ids)
    sent = 0
    failed = 0

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
            logger.error(f"Échec envoi à {user.email} : {e}")
            failed += 1

    logger.info(f"Email en masse : {sent} envoyés, {failed} échoués")
    return f"{sent}/{users.count()} emails envoyés"


@shared_task
def send_daily_producer_report():
    """Rapport quotidien des ventes aux producteurs"""
    today = timezone.now().date()
    producers = Utilisateur.objects.filter(role='PRODUCTEUR')

    reports_sent = 0
    for producer in producers:
        orders = Order.objects.filter(
            items__product__producer__user=producer,
            created_at__date=today
        ).distinct()

        if orders.exists():
            total_sales = orders.aggregate(total=Sum('total_amount'))['total'] or 0

            send_mail(
                subject=f"Rapport quotidien - {today.strftime('%d/%m/%Y')}",
                message=f"Bonjour {producer.get_full_name() or producer.username},\n\n"
                        f"Aujourd'hui, vous avez reçu {orders.count()} commande(s) pour un total de {total_sales:.2f}€.\n\n"
                        f"Consultez votre dashboard pour plus de détails.\n\n"
                        f"L'équipe AgriBusiness",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[producer.email],
            )
            reports_sent += 1

    logger.info(f"Rapports quotidiens envoyés à {reports_sent} producteurs")
    return f"{reports_sent} rapports envoyés"