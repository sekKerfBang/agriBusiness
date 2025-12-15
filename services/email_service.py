from django.core.mail import send_mail
from django.template.loader import render_to_string
from asgiref.sync import async_to_sync
from anymail.message import AnymailMessage
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

class AsyncEmailService:
    """Service email 100% async"""
    
    @staticmethod
    @async_to_sync
    async def send_template_email(to_email, subject, template_name, context=None):
        """Envoie un email avec template HTML"""
        try:
            html_content = render_to_string(f'emails/{template_name}.html', context or {})
            
            msg = AnymailMessage(
                subject=subject,
                body=html_content,
                from_email='noreply@agrimarket.com',
                to=[to_email],
            )
            msg.content_subtype = "html"
            
            # Send async
            await msg.send_async()
            logger.info(f"Email envoyé à {to_email} : {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur email: {e}")
            return False
    
    @staticmethod
    def send_welcome_email(user):
        """Email de bienvenue"""
        return AsyncEmailService.send_template_email(
            user.email,
            "Bienvenue sur AgriMarket !",
            "welcome",
            {'user': user, 'login_url': "https://agrimarket.com/login"}
        )
    
    @staticmethod
    def send_order_confirmation(order):
        """Email de confirmation de commande"""
        return AsyncEmailService.send_template_email(
            order.client.email,
            f"Confirmation commande #{order.order_number}",
            "order_confirmation",
            {
                'order': order,
                'items': order.items.all(),
                'total': order.total_amount,
            }
        )
    
    @staticmethod
    def send_low_stock_alert(producer, products):
        """Alerte stock bas"""
        return AsyncEmailService.send_template_email(
            producer.email,
            "⚠️ Alertes stock bas sur vos produits",
            "low_stock",
            {'producer': producer, 'products': products}
        )


# from django.core.mail import send_mail
# from asgiref.sync import async_to_sync
# from anymail.message import AnymailMessage
# from functools import partial
# import logging

# logger = logging.getLogger(__name__)

# # Partial function pour config email de base
# base_email_config = partial(
#     send_mail,
#     fail_silently=False,
#     html_message=None
# )

# class AsyncEmailService:
#     """Service email 100% async pour Django 6.0"""
    
#     @staticmethod
#     @async_to_sync
#     async def send_welcome_email(user):
#         """Envoi asynchrone d'email de bienvenue"""
#         try:
#             msg = AnymailMessage(
#                 subject="Bienvenue sur AgriMarket !",
#                 body=f"Bonjour {user.username},\n\nVotre compte producteur a été validé.",
#                 from_email="welcome@agrimarket.com",
#                 to=[user.email],
#             )
#             msg.content_subtype = "html"
#             msg.send()
#             logger.info(f"Email de bienvenue envoyé à {user.email}")
#         except Exception as e:
#             logger.error(f"Erreur email: {e}")
    
#     @staticmethod
#     @async_to_sync
#     async def send_order_confirmation(order):
#         """Confirmation de commande async"""
#         items = order.items.all()
#         html_content = f"""
#         <h1>Commande #{order.order_number}</h1>
#         <p>Montant: {order.total_amount}€</p>
#         <ul>
#             {''.join(f"<li>{item.product.name} x{item.quantity}</li>" for item in items)}
#         </ul>
#         """
#         await AsyncEmailService.send_templated_email(
#             to=order.client.email,
#             subject=f"Confirmation commande #{order.order_number}",
#             body=html_content
#         )

# # Partial functions pour créer des templates d'email rapidement
# send_producer_validation_email = partial(
#     AsyncEmailService.send_templated_email,
#     subject="Votre compte producteur est validé !",
#     template="emails/producer_validated.html"
# )

# send_low_stock_alert = partial(
#     AsyncEmailService.send_templated_email,
#     subject="⚠️ Alertes stock bas",
#     template="emails/low_stock.html"
# )