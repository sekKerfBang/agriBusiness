from django.db import transaction
from django.contrib.auth import get_user_model
from .models import ProducerProfile
from services.email_service import AsyncEmailService
from tasks.email_tasks import send_bulk_notification_task

User = get_user_model()

class UtilisateurService:
    """Service layer pour la gestion des utilisateurs"""
    
    @staticmethod
    @transaction.atomic
    def register_producer(user_data, producer_data):
        """Enregistre un nouveau producteur avec validation"""
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password'],
            role='PRODUCTEUR',
            phone=user_data.get('phone', '')
        )
        
        producer = ProducerProfile.objects.create(
            user=user,
            farm_name=producer_data['farm_name'],
            siret=producer_data['siret'],
            is_organic=producer_data.get('is_organic', False),
            description=producer_data.get('description', ''),
            latitude=producer_data.get('latitude'),
            longitude=producer_data.get('longitude')
        )
        
        # Email de bienvenue async
        AsyncEmailService.send_welcome_email(user)
        
        return user, producer
    
    @staticmethod
    def get_producer_stats(producer_id):
        """Récupère les stats d'un producteur"""
        from apps.products.models import Product
        from apps.orders.models import Order
        
        products = Product.objects.filter(producer_id=producer_id)
        orders = Order.objects.filter(items__product__producer_id=producer_id).distinct()
        
        return {
            'total_products': products.count(),
            'active_products': products.filter(is_active=True).count(),
            'total_orders': orders.count(),
            'revenue': sum(o.total_amount for o in orders.filter(status='DELIVERED')),
            'stock_alerts': products.filter(stock__lt=10).count()
        }
    
    @staticmethod
    def notify_all_producers(subject, message):
        """Envoie une notification à tous les producteurs"""
        producer_ids = User.objects.filter(role='PRODUCTEUR').values_list('id', flat=True)
        send_bulk_notification_task.delay(list(producer_ids), subject, message)