import logging
from typing import List, Dict, Any
from celery import shared_task, group
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Q, Count
from django.core.cache import cache

from apps.orders.models import Order
from apps.utilisateur.models import Utilisateur
from apps.products.models import Product
from services.email_service import EmailService
from services.notification_service import NotificationService

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_task(self, order_id: int) -> Dict[str, Any]:
    """
    Tâche pour envoyer la confirmation de commande
    """
    try:
        # Récupérer la commande avec optimisations
        order = Order.objects.select_related(
            'client'
        ).prefetch_related(
            'items__product__producer__user'
        ).get(id=order_id)
        
        # Envoyer l'email de confirmation
        email_sent = EmailService.send_order_confirmation(order)
        
        if email_sent:
            # Notifier les producteurs
            NotificationService.notify_new_order(order)
            
            logger.info(f"✅ Commande #{order.order_number} : email envoyé à {order.client.email}")
            
            return {
                'success': True,
                'order_id': order_id,
                'order_number': order.order_number,
                'client_email': order.client.email,
                'message': 'Confirmation envoyée avec succès'
            }
        else:
            logger.error(f"❌ Échec envoi email commande #{order.order_number}")
            return {
                'success': False,
                'order_id': order_id,
                'message': 'Échec envoi email'
            }
            
    except Order.DoesNotExist:
        logger.error(f"❌ Commande {order_id} introuvable")
        return {
            'success': False,
            'order_id': order_id,
            'message': 'Commande introuvable'
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur tâche confirmation commande {order_id} : {e}")
        # Retry avec exponential backoff
        raise self.retry(exc=e, countdown=self.default_retry_delay ** self.request.retries)


@shared_task(bind=True, rate_limit='50/m', max_retries=2)
def send_bulk_newsletter_task(
    self,
    user_ids: List[int],
    subject: str,
    template_name: str,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Envoi de newsletter en masse avec rate limiting
    """
    try:
        context = context or {}
        
        # Récupérer les utilisateurs valides
        users = Utilisateur.objects.filter(
            id__in=user_ids,
            is_active=True,
            email__isnull=False
        ).exclude(
            email=''
        ).only('id', 'email', 'username')
        
        total_users = users.count()
        
        if total_users == 0:
            return {'sent': 0, 'failed': 0, 'total': 0}
        
        # Diviser en chunks pour éviter les timeouts
        chunk_size = 100
        chunks = []
        
        for i in range(0, total_users, chunk_size):
            chunk = users[i:i + chunk_size]
            chunks.append([user.email for user in chunk])
        
        # Créer les sous-tâches
        subtasks = []
        for chunk in chunks:
            subtask = send_email_chunk_task.s(
                emails=chunk,
                subject=subject,
                template_name=template_name,
                context=context
            )
            subtasks.append(subtask)
        
        # Exécuter en parallèle
        job = group(subtasks)
        result = job.apply_async()
        
        # Attendre les résultats
        results = result.get(disable_sync_subtasks=False, propagate=False)
        
        # Compiler les résultats
        total_sent = sum(r['sent'] for r in results if isinstance(r, dict))
        total_failed = sum(r['failed'] for r in results if isinstance(r, dict))
        
        logger.info(f"📧 Newsletter envoyée : {total_sent} succès, {total_failed} échecs")
        
        return {
            'sent': total_sent,
            'failed': total_failed,
            'total': total_users,
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur newsletter : {e}")
        raise self.retry(exc=e)


@shared_task
def send_email_chunk_task(
    emails: List[str],
    subject: str,
    template_name: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Sous-tâche pour envoyer un chunk d'emails
    """
    sent = 0
    failed = []
    
    for email in emails:
        try:
            success = EmailService.send_template_email(
                recipient_email=email,
                subject=subject,
                template_name=template_name,
                context=context
            )
            
            if success:
                sent += 1
            else:
                failed.append(email)
                
        except Exception as e:
            logger.warning(f"Échec email {email} : {e}")
            failed.append(email)
    
    return {
        'sent': sent,
        'failed': failed,
        'chunk_size': len(emails)
    }


@shared_task
def send_daily_sales_report() -> Dict[str, Any]:
    """
    Rapport quotidien des ventes pour les producteurs
    """
    today = timezone.now().date()
    yesterday = today - timezone.timedelta(days=1)
    
    # Récupérer tous les producteurs actifs
    producers = Utilisateur.objects.filter(
        role='PRODUCTEUR',
        is_active=True
    ).select_related('producer_profile')
    
    reports_sent = 0
    reports_failed = 0
    
    for producer in producers:
        try:
            # Récupérer les commandes de la veille
            orders = Order.objects.filter(
                items__product__producer__user=producer,
                created_at__date=yesterday,
                status__in=['CONFIRMED', 'SHIPPED', 'DELIVERED']
            ).distinct()
            
            if not orders.exists():
                continue
            
            # Calculer les statistiques
            stats = orders.aggregate(
                total_sales=Sum('total_amount'),
                total_orders=Count('id'),
                total_items=Sum('items__quantity')
            )
            
            # Récupérer les produits vendus
            sold_products = Product.objects.filter(
                producer__user=producer,
                order_items__order__in=orders
            ).distinct().annotate(
                quantity_sold=Sum('order_items__quantity')
            ).order_by('-quantity_sold')[:10]
            
            # Envoyer le rapport
            success = EmailService.send_template_email(
                recipient_email=producer.email,
                subject=f"📊 Rapport quotidien - {yesterday.strftime('%d/%m/%Y')}",
                template_name='daily_sales_report',
                context={
                    'producer': producer,
                    'date': yesterday,
                    'stats': stats,
                    'orders_count': orders.count(),
                    'sold_products': sold_products,
                    'today': today
                }
            )
            
            if success:
                reports_sent += 1
                # Notification in-app
                NotificationService.create_notification(
                    user_id=producer.id,
                    title="📊 Rapport quotidien disponible",
                    message=f"Votre rapport de ventes du {yesterday.strftime('%d/%m/%Y')} a été envoyé par email.",
                    notification_type='INFO'
                )
            else:
                reports_failed += 1
                
        except Exception as e:
            logger.error(f"❌ Erreur rapport producteur {producer.id} : {e}")
            reports_failed += 1
    
    logger.info(f"📊 Rapports quotidiens : {reports_sent} envoyés, {reports_failed} échecs")
    
    return {
        'reports_sent': reports_sent,
        'reports_failed': reports_failed,
        'total_producers': producers.count(),
        'date': yesterday.isoformat()
    }


@shared_task
def send_welcome_emails_to_new_users() -> Dict[str, Any]:
    """
    Envoie des emails de bienvenue aux nouveaux utilisateurs
    (À exécuter quotidiennement)
    """
    yesterday = timezone.now().date() - timezone.timedelta(days=1)
    
    # Récupérer les nouveaux utilisateurs d'hier
    new_users = Utilisateur.objects.filter(
        date_joined__date=yesterday,
        is_active=True,
        email__isnull=False
    ).exclude(email='')
    
    emails_sent = 0
    
    for user in new_users:
        try:
            # Envoyer l'email de bienvenue
            success = EmailService.send_welcome_email(user)
            
            if success:
                emails_sent += 1
                # Notification in-app
                NotificationService.create_notification(
                    user_id=user.id,
                    title="🎉 Bienvenue sur AgriBusiness !",
                    message="Merci de nous avoir rejoint. Découvrez toutes nos fonctionnalités.",
                    notification_type='INFO'
                )
                
        except Exception as e:
            logger.error(f"❌ Erreur email bienvenue user {user.id} : {e}")
    
    logger.info(f"👋 Emails bienvenue : {emails_sent}/{new_users.count()} envoyés")
    
    return {
        'emails_sent': emails_sent,
        'total_new_users': new_users.count(),
        'date': yesterday.isoformat()
    }


@shared_task(bind=True, max_retries=2)
def send_password_reset_task(self, user_id: int, reset_url: str) -> bool:
    """
    Envoie l'email de réinitialisation de mot de passe
    """
    try:
        user = Utilisateur.objects.get(id=user_id, is_active=True)
        
        success = EmailService.send_password_reset(user, reset_url)
        
        if success:
            logger.info(f"🔒 Email réinitialisation envoyé à {user.email}")
            return True
        else:
            logger.error(f"❌ Échec email réinitialisation user {user.id}")
            return False
            
    except Utilisateur.DoesNotExist:
        logger.error(f"❌ User {user_id} introuvable")
        return False
        
    except Exception as e:
        logger.error(f"❌ Erreur tâche réinitialisation : {e}")
        raise self.retry(exc=e)




# # tasks/email_tasks.py

# from celery import shared_task
# from celery.utils.log import get_task_logger
# from django.core.mail import send_mail
# from django.template.loader import render_to_string
# from django.conf import settings
# from django.utils import timezone
# from django.db.models import Sum
# from apps.orders.models import Order
# from apps.utilisateur.models import Utilisateur

# logger = get_task_logger(__name__)

# @shared_task(bind=True, max_retries=5, retry_backoff=True)
# def send_order_confirmation_task(self, order_id: int):
#     """Envoie l'email de confirmation de commande au client"""
#     try:
#         order = Order.objects.select_related('client').prefetch_related('items__product').get(id=order_id)

#         html_message = render_to_string('emails/order_confirmation.html', {
#             'order': order,
#             'items': order.items.all(),
#             'total': order.total_amount,
#         })

#         send_mail(
#             subject=f"Votre commande #{order.order_number} est confirmée !",
#             message="Votre commande a été confirmée avec succès.",
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[order.client.email],
#             html_message=html_message,
#             fail_silently=False,
#         )

#         logger.info(f"Email confirmation envoyé pour commande #{order.order_number}")
#         return f"Confirmation envoyée à {order.client.email}"

#     except Order.DoesNotExist:
#         logger.error(f"Commande {order_id} introuvable")
#         return "Commande introuvable"
#     except Exception as e:
#         logger.error(f"Erreur envoi email confirmation {order_id} : {e}")
#         raise self.retry(exc=e)


# @shared_task(bind=True, rate_limit='20/m')
# def send_bulk_notification_task(self, user_ids: list, subject: str, message: str):
#     """Envoi d'emails en masse (newsletter, promo, etc.)"""
#     users = Utilisateur.objects.filter(id__in=user_ids)
#     sent = 0
#     failed = 0

#     for user in users:
#         try:
#             send_mail(
#                 subject=subject,
#                 message=message,
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 recipient_list=[user.email],
#                 fail_silently=False,
#             )
#             sent += 1
#         except Exception as e:
#             logger.error(f"Échec envoi à {user.email} : {e}")
#             failed += 1

#     logger.info(f"Email en masse : {sent} envoyés, {failed} échoués")
#     return f"{sent}/{users.count()} emails envoyés"


# @shared_task
# def send_daily_producer_report():
#     """Rapport quotidien des ventes aux producteurs"""
#     today = timezone.now().date()
#     producers = Utilisateur.objects.filter(role='PRODUCTEUR')

#     reports_sent = 0
#     for producer in producers:
#         orders = Order.objects.filter(
#             items__product__producer__user=producer,
#             created_at__date=today
#         ).distinct()

#         if orders.exists():
#             total_sales = orders.aggregate(total=Sum('total_amount'))['total'] or 0

#             send_mail(
#                 subject=f"Rapport quotidien - {today.strftime('%d/%m/%Y')}",
#                 message=f"Bonjour {producer.get_full_name() or producer.username},\n\n"
#                         f"Aujourd'hui, vous avez reçu {orders.count()} commande(s) pour un total de {total_sales:.2f}€.\n\n"
#                         f"Consultez votre dashboard pour plus de détails.\n\n"
#                         f"L'équipe AgriBusiness",
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 recipient_list=[producer.email],
#             )
#             reports_sent += 1

#     logger.info(f"Rapports quotidiens envoyés à {reports_sent} producteurs")
#     return f"{reports_sent} rapports envoyés"