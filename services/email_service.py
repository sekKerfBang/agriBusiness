# services/email_service.py

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from asgiref.sync import async_to_sync
from anymail.message import AnymailMessage
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class AsyncEmailService:
    """Service d'envoi d'emails asynchrone avec Anymail"""

    @staticmethod
    @async_to_sync
    async def send_template_email(to_email: str, subject: str, template_name: str, context: dict = None):
        """Envoie un email HTML avec template"""
        try:
            context = context or {}
            html_content = render_to_string(f"emails/{template_name}.html", context)
            text_content = strip_tags(html_content)  # Version texte brut

            message = AnymailMessage(
                subject=subject,
                body=text_content,
                to=[to_email],
                from_email=settings.DEFAULT_FROM_EMAIL,
            )
            message.attach_alternative(html_content, "text/html")

            await message.asend()  # Anymail utilise asend() pour l'async
            logger.info(f"Email envoyé à {to_email} : {subject}")
            return True

        except Exception as e:
            logger.error(f"Erreur envoi email à {to_email} : {e}")
            return False

    @staticmethod
    def send_welcome_email(user):
        return AsyncEmailService.send_template_email(
            to_email=user.email,
            subject="Bienvenue sur AgriBusiness ! 🌱",
            template_name="welcome",
            context={'user': user}
        )

    @staticmethod
    def send_order_confirmation(order):
        return AsyncEmailService.send_template_email(
            to_email=order.client.email,
            subject=f"Confirmation de votre commande #{order.order_number}",
            template_name="order_confirmation",
            context={
                'order': order,
                'items': order.items.all(),
                'total': order.total_amount,
            }
        )

    @staticmethod
    def send_low_stock_alert(producer, products):
        return AsyncEmailService.send_template_email(
            to_email=producer.user.email,
            subject="⚠️ Alerte : Stock faible sur vos produits",
            template_name="low_stock_alert",
            context={
                'producer': producer,
                'products': products,
            }
        )

    @staticmethod
    def send_new_order_alert(order):
        """Email au producteur quand une commande est passée"""
        # On envoie à chaque producteur concerné
        producers = set(item.product.producer.user for item in order.items.all())
        for producer in producers:
            AsyncEmailService.send_template_email(
                to_email=producer.email,
                subject=f"Nouvelle commande #{order.order_number}",
                template_name="new_order_producer",
                context={
                    'order': order,
                    'producer': producer,
                }
            )



# from django.core.mail import send_mail
# from django.template.loader import render_to_string
# from asgiref.sync import async_to_sync
# from anymail.message import AnymailMessage
# from celery import shared_task
# import logging

# logger = logging.getLogger(__name__)

# class AsyncEmailService:
#     """Service email 100% async"""
    
#     @staticmethod
#     @async_to_sync
#     async def send_template_email(to_email, subject, template_name, context=None):
#         """Envoie un email avec template HTML"""
#         try:
#             html_content = render_to_string(f'emails/{template_name}.html', context or {})
            
#             msg = AnymailMessage(
#                 subject=subject,
#                 body=html_content,
#                 from_email='noreply@agrimarket.com',
#                 to=[to_email],
#             )
#             msg.content_subtype = "html"
            
#             # Send async
#             await msg.send_async()
#             logger.info(f"Email envoyé à {to_email} : {subject}")
#             return True
            
#         except Exception as e:
#             logger.error(f"Erreur email: {e}")
#             return False
    
#     @staticmethod
#     def send_welcome_email(user):
#         """Email de bienvenue"""
#         return AsyncEmailService.send_template_email(
#             user.email,
#             "Bienvenue sur AgriMarket !",
#             "welcome",
#             {'user': user, 'login_url': "https://agrimarket.com/login"}
#         )
    
#     @staticmethod
#     def send_order_confirmation(order):
#         """Email de confirmation de commande"""
#         return AsyncEmailService.send_template_email(
#             order.client.email,
#             f"Confirmation commande #{order.order_number}",
#             "order_confirmation",
#             {
#                 'order': order,
#                 'items': order.items.all(),
#                 'total': order.total_amount,
#             }
#         )
    
#     @staticmethod
#     def send_low_stock_alert(producer, products):
#         """Alerte stock bas"""
#         return AsyncEmailService.send_template_email(
#             producer.email,
#             "⚠️ Alertes stock bas sur vos produits",
#             "low_stock",
#             {'producer': producer, 'products': products}
#         )

