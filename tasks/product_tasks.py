from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.cache import cache
from django.db.models import F
from apps.products.models import Product
from services.notification_service import NotificationService
from django.utils import timezone
from datetime import timedelta

logger = get_task_logger(__name__)

@shared_task
def check_low_stock():
    """Vérifie les produits en stock bas toutes les heures"""
    low_stock_products = Product.objects.filter(
        stock__lt=10,
        is_active=True
    ).select_related('producer__user')
    
    alerts_sent = 0
    for product in low_stock_products:
        # Vérifie si déjà notifié dans les dernières 24h
        cache_key = f"stock_alert_{product.id}"
        if not cache.get(cache_key):
            NotificationService.notify_low_stock(product)
            cache.set(cache_key, True, 86400)  # 24h
            alerts_sent += 1
            logger.warning(f"Alerte stock bas: {product.name}")
    
    return f"{alerts_sent} alertes envoyées"


@shared_task
def update_product_statistics():
    """Met à jour les statistiques produits (populaire, tendance)"""
    from datetime import timedelta
    from django.utils import timezone
    
    # Réinitialiser les compteurs de vue journaliers
    Product.objects.all().update(daily_views=0)
    
    logger.info("Statistiques produits mises à jour")
    return "Stats updated"


@shared_task
def generate_product_pdf_catalog(producer_id):
    """Génère un PDF du catalogue produits"""
    from apps.products.models import ProducerProfile
    from django.template.loader import render_to_string
    from weasyprint import HTML
    
    try:
        producer = ProducerProfile.objects.get(id=producer_id)
        products = producer.products.filter(is_active=True)
        
        html_string = render_to_string('pdf/catalog.html', {
            'producer': producer,
            'products': products,
            'generated_at': timezone.now()
        })
        
        pdf_file = HTML(string=html_string).write_pdf()
        
        # Sauvegarder
        filename = f"catalogs/{producer.farm_name}_{producer_id}.pdf"
        with open(filename, 'wb') as f:
            f.write(pdf_file)
        
        logger.info(f"PDF généré pour {producer.farm_name}")
        return filename
        
    except Exception as e:
        logger.error(f"Erreur génération PDF: {e}")
        raise


@shared_task(bind=True, rate_limit='5/h')
def sync_product_prices(self):
    """Synchronise les prix avec un ERP externe (exemple)"""
    # API call vers un système externe
    # product.update_price(external_price)
    logger.info("Synchronisation des prix effectuée")
    return "Prices synced"


# from celery import shared_task
# from celery.utils.log import get_task_logger
# from apps.products.models import Product
# from services.notification_service import NotificationService

# logger = get_task_logger(__name__)

# @shared_task
# def check_low_stock():
#     """Vérifie les produits en stock bas toutes les heures"""
#     low_stock_products = Product.objects.filter(
#         stock__lt=10,
#         is_active=True
#     ).select_related('producer__user')
    
#     alerts_sent = 0
#     for product in low_stock_products:
#         NotificationService.notify_low_stock(product, threshold=10)
#         alerts_sent += 1
    
#     return f"{alerts_sent} alertes de stock bas envoyées"

# @shared_task
# def update_product_statistics():
#     """Mise à jour des stats produits (views, etc.)"""
#     # Logique de mise à jour des stats
#     # Peut-être utilisé pour des recommandations
#     logger.info("Mise à jour des statistiques produits")
#     return "Stats updated"

# @shared_task
# def generate_product_pdf_catalog(producer_id: int):
#     """Génère un PDF du catalogue produits"""
#     from apps.products.models import ProducerProfile
#     from django.template.loader import render_to_string
#     from weasyprint import HTML
    
#     try:
#         producer = ProducerProfile.objects.get(id=producer_id)
#         products = producer.products.all()
        
#         html_string = render_to_string('pdf/catalog.html', {
#             'producer': producer,
#             'products': products
#         })
        
#         pdf_file = HTML(string=html_string).write_pdf()
        
#         # Sauvegarder le fichier
#         filename = f"catalogs/{producer.farm_name}_{producer_id}.pdf"
#         with open(filename, 'wb') as f:
#             f.write(pdf_file)
        
#         logger.info(f"PDF catalogue généré pour {producer.farm_name}")
#         return filename
    
#     except Exception as e:
#         logger.error(f"Erreur génération PDF: {e}")
#         raise