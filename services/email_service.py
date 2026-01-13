import logging
from typing import List, Optional, Dict, Any
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

logger = logging.getLogger(__name__)


class EmailService:
    """Service d'email natif utilisant Django SMTP"""
    
    @staticmethod
    def send_email(
        subject: str,
        plain_message: str,
        html_message: Optional[str] = None,
        from_email: Optional[str] = None,
        recipient_list: List[str] = None,
        cc_list: List[str] = None,
        bcc_list: List[str] = None,
        attachments: List[Dict[str, Any]] = None,
        connection=None
    ) -> bool:
        """
        Envoie un email avec support HTML et pièces jointes
        """
        try:
            recipient_list = recipient_list or []
            from_email = from_email or settings.DEFAULT_FROM_EMAIL
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=from_email,
                to=recipient_list,
                cc=cc_list or [],
                bcc=bcc_list or [],
                connection=connection
            )
            
            if html_message:
                email.attach_alternative(html_message, "text/html")
            
            if attachments:
                for attachment in attachments:
                    email.attach(
                        filename=attachment.get('filename'),
                        content=attachment.get('content'),
                        mimetype=attachment.get('mimetype')
                    )
            
            email.send(fail_silently=False)
            logger.info(f"✅ Email envoyé à {recipient_list} : {subject}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi email à {recipient_list} : {e}")
            return False
    
    @staticmethod
    def send_template_email(
        recipient_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any] = None,
        from_email: Optional[str] = None,
        lang: str = 'fr'
    ) -> bool:
        """
        Envoie un email basé sur un template Django
        """
        try:
            # Chercher le template avec support multi-langue
            template_path = f"emails/{lang}/{template_name}.html"
            
            # Rendre le template HTML
            html_content = render_to_string(template_path, context or {})
            
            # Créer une version texte
            text_content = strip_tags(html_content)
            
            # Envoyer l'email
            return EmailService.send_email(
                subject=subject,
                plain_message=text_content,
                html_message=html_content,
                from_email=from_email,
                recipient_list=[recipient_email]
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur template email à {recipient_email} : {e}")
            return False
    
    @staticmethod
    def send_bulk_emails(
        recipient_emails: List[str],
        subject: str,
        plain_message: str,
        html_message: Optional[str] = None,
        batch_size: int = 50
    ) -> Dict[str, int]:
        """
        Envoie des emails en masse avec connexion persistante
        """
        results = {
            'sent': 0,
            'failed': 0,
            'total': len(recipient_emails)
        }
        
        if not recipient_emails:
            return results
        
        try:
            # Ouvrir une connexion persistante
            connection = get_connection(
                fail_silently=False,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                timeout=30  # Timeout de 30 secondes
            )
            
            connection.open()
            
            # Diviser en batchs
            for i in range(0, len(recipient_emails), batch_size):
                batch = recipient_emails[i:i + batch_size]
                
                try:
                    # Utiliser BCC pour envoyer à tout le batch en une fois
                    email = EmailMultiAlternatives(
                        subject=subject,
                        body=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[settings.DEFAULT_FROM_EMAIL],  # Destinataire visible
                        bcc=batch,  # Destinataires cachés
                        connection=connection
                    )
                    
                    if html_message:
                        email.attach_alternative(html_message, "text/html")
                    
                    email.send(fail_silently=False)
                    results['sent'] += len(batch)
                    
                    logger.info(f"✅ Batch {i//batch_size + 1} envoyé : {len(batch)} emails")
                    
                except Exception as e:
                    logger.error(f"❌ Erreur batch {i//batch_size + 1} : {e}")
                    results['failed'] += len(batch)
            
            connection.close()
            
        except Exception as e:
            logger.error(f"❌ Erreur connexion email bulk : {e}")
            results['failed'] = results['total']
        
        return results
    
    # Méthodes spécifiques au domaine
    @classmethod
    def send_order_confirmation(cls, order) -> bool:
        """Email de confirmation de commande"""
        return cls.send_template_email(
            recipient_email=order.client.email,
            subject=f"✅ Confirmation de commande #{order.order_number}",
            template_name='order_confirmation',
            context={
                'order': order,
                'items': order.items.all(),
                'total_amount': order.total_amount,
                'delivery_date': order.delivery_date,
                'client': order.client
            }
        )
    
    @classmethod
    def send_low_stock_alert(cls, producer, products: List) -> bool:
        """Alerte stock bas"""
        return cls.send_template_email(
            recipient_email=producer.user.email,
            subject=f"⚠️ Alerte : Stock faible sur {len(products)} produit(s)",
            template_name='low_stock_alert',
            context={
                'producer': producer,
                'products': products,
                'alert_date': timezone.now(),
                'threshold': 10
            }
        )
    
    @classmethod
    def send_welcome_email(cls, user) -> bool:
        """Email de bienvenue"""
        return cls.send_template_email(
            recipient_email=user.email,
            subject="🎉 Bienvenue sur AgroBusiness !",
            template_name='welcome',
            context={
                'user': user,
                'welcome_date': timezone.now(),
                'platform_name': 'AgroBusiness'
            }
        )
    
    @classmethod
    def send_password_reset(cls, user, reset_url: str) -> bool:
        """Email de réinitialisation de mot de passe"""
        return cls.send_template_email(
            recipient_email=user.email,
            subject="🔒 Réinitialisation de votre mot de passe",
            template_name='password_reset',
            context={
                'user': user,
                'reset_url': reset_url,
                'expiry_hours': 24
            }
        )



# # services/email_service.py

# from django.core.mail import send_mail
# from django.template.loader import render_to_string
# from django.utils.html import strip_tags
# from asgiref.sync import async_to_sync
# from anymail.message import AnymailMessage
# from django.conf import settings
# import logging

# logger = logging.getLogger(__name__)

# class AsyncEmailService:
#     """Service d'envoi d'emails asynchrone avec Anymail"""

#     @staticmethod
#     @async_to_sync
#     async def send_template_email(to_email: str, subject: str, template_name: str, context: dict = None):
#         """Envoie un email HTML avec template"""
#         try:
#             context = context or {}
#             html_content = render_to_string(f"emails/{template_name}.html", context)
#             text_content = strip_tags(html_content)  # Version texte brut

#             message = AnymailMessage(
#                 subject=subject,
#                 body=text_content,
#                 to=[to_email],
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#             )
#             message.attach_alternative(html_content, "text/html")

#             await message.asend()  # Anymail utilise asend() pour l'async
#             logger.info(f"Email envoyé à {to_email} : {subject}")
#             return True

#         except Exception as e:
#             logger.error(f"Erreur envoi email à {to_email} : {e}")
#             return False

#     @staticmethod
#     def send_welcome_email(user):
#         return AsyncEmailService.send_template_email(
#             to_email=user.email,
#             subject="Bienvenue sur AgriBusiness ! 🌱",
#             template_name="welcome",
#             context={'user': user}
#         )

#     @staticmethod
#     def send_order_confirmation(order):
#         return AsyncEmailService.send_template_email(
#             to_email=order.client.email,
#             subject=f"Confirmation de votre commande #{order.order_number}",
#             template_name="order_confirmation",
#             context={
#                 'order': order,
#                 'items': order.items.all(),
#                 'total': order.total_amount,
#             }
#         )

#     @staticmethod
#     def send_low_stock_alert(producer, products):
#         return AsyncEmailService.send_template_email(
#             to_email=producer.user.email,
#             subject="⚠️ Alerte : Stock faible sur vos produits",
#             template_name="low_stock_alert",
#             context={
#                 'producer': producer,
#                 'products': products,
#             }
#         )

#     @staticmethod
#     def send_new_order_alert(order):
#         """Email au producteur quand une commande est passée"""
#         # On envoie à chaque producteur concerné
#         producers = set(item.product.producer.user for item in order.items.all())
#         for producer in producers:
#             AsyncEmailService.send_template_email(
#                 to_email=producer.email,
#                 subject=f"Nouvelle commande #{order.order_number}",
#                 template_name="new_order_producer",
#                 context={
#                     'order': order,
#                     'producer': producer,
#                 }
#             )


