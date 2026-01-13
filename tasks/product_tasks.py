# tasks/product_tasks.py

import logging
import os
from typing import Dict, Any, Optional
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Count, F, Q
from django.core.cache import cache
import tempfile

from apps.products.models import Product, ProducerProfile
from apps.orders.models import Order
from services.notification_service import NotificationService
from services.email_service import EmailService

logger = get_task_logger(__name__)


@shared_task
def check_and_update_product_statistics() -> Dict[str, Any]:
    """
    Met à jour les statistiques des produits et réinitialise les compteurs quotidiens
    """
    try:
        # 1. Réinitialiser les vues quotidiennes
        updated_views = Product.objects.filter(
            daily_views__gt=0
        ).update(daily_views=0)
        
        # 2. Mettre à jour la popularité basée sur les ventes des 30 derniers jours
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        
        # Récupérer les produits avec leurs ventes récentes
        products_with_sales = Product.objects.filter(
            is_active=True,
            order_items__order__created_at__gte=thirty_days_ago,
            order_items__order__status__in=['CONFIRMED', 'SHIPPED', 'DELIVERED']
        ).annotate(
            recent_sales=Sum('order_items__quantity'),
            recent_orders=Count('order_items__order', distinct=True)
        ).distinct()
        
        products_updated = 0
        
        for product in products_with_sales:
            # Calculer un score de popularité
            popularity_score = (
                (product.recent_sales or 0) * 10 +  # Poids pour les ventes
                (product.total_views or 0) * 0.1 +   # Poids pour les vues
                (product.average_rating or 0) * 5    # Poids pour les avis
            )
            
            # Mettre à jour si le score a changé significativement
            if abs((product.popularity_score or 0) - popularity_score) > 0.1:
                product.popularity_score = popularity_score
                product.save(update_fields=['popularity_score'])
                products_updated += 1
        
        # 3. Marquer les produits tendance
        # Un produit est tendance s'il a eu des ventes significatives récentes
        trending_products = products_with_sales.filter(
            recent_sales__gte=10  # Au moins 10 ventes récentes
        ).update(is_trending=True)
        
        # Désactiver is_trending pour les autres
        Product.objects.exclude(
            id__in=products_with_sales.filter(recent_sales__gte=10).values('id')
        ).update(is_trending=False)
        
        logger.info(f"📊 Stats produits : {updated_views} vues réinitialisées, "
                   f"{products_updated} popularités mises à jour")
        
        return {
            'views_reset': updated_views,
            'popularity_updated': products_updated,
            'trending_products': trending_products,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour stats produits : {e}")
        return {
            'error': str(e),
            'views_reset': 0,
            'popularity_updated': 0
        }


@shared_task(bind=True, max_retries=3)
def generate_product_catalog_pdf(self, producer_id: int) -> Dict[str, Any]:
    """
    Génère un catalogue PDF pour un producteur
    Version native avec reportlab
    """
    try:
        from io import BytesIO
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        producer = ProducerProfile.objects.select_related('user').get(id=producer_id)
        products = producer.products.filter(is_active=True).order_by('category__name', 'name')
        
        if not products.exists():
            return {
                'success': False,
                'message': 'Aucun produit actif',
                'producer_id': producer_id
            }
        
        # Créer le buffer pour le PDF
        buffer = BytesIO()
        
        # Créer le document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50')
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#34495e')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading3'],
            fontSize=14,
            spaceAfter=10,
            spaceBefore=20,
            textColor=colors.HexColor('#2980b9')
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        # Contenu du document
        story = []
        
        # Titre
        story.append(Paragraph(f"Catalogue Produits", title_style))
        story.append(Paragraph(f"{producer.farm_name}", subtitle_style))
        story.append(Paragraph(f"Généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}", normal_style))
        story.append(Spacer(1, 20))
        
        # Informations du producteur
        story.append(Paragraph("Informations du producteur", heading_style))
        producer_info = [
            f"<b>Nom :</b> {producer.user.get_full_name() or producer.user.username}",
            f"<b>Exploitation :</b> {producer.farm_name}",
            f"<b>Localisation :</b> {producer.location or 'Non spécifiée'}",
            f"<b>Contact :</b> {producer.user.email}",
            f"<b>Téléphone :</b> {producer.phone or 'Non spécifié'}"
        ]
        
        for info in producer_info:
            story.append(Paragraph(info, normal_style))
        
        story.append(Spacer(1, 30))
        
        # Produits par catégorie
        current_category = None
        
        for product in products:
            if product.category and product.category.name != current_category:
                current_category = product.category.name
                story.append(Paragraph(f"Catégorie : {current_category}", heading_style))
                story.append(Spacer(1, 10))
            
            # Informations produit
            product_text = f"""
            <b>{product.name}</b><br/>
            {product.description[:100]}...<br/>
            <b>Prix :</b> {product.price} €/{product.unit or 'unité'} 
            <b>Stock :</b> {product.stock} unités
            <b>Bio :</b> {'✅' if product.is_organic else '❌'}
            """
            
            story.append(Paragraph(product_text, normal_style))
            story.append(Spacer(1, 15))
        
        # Pied de page
        story.append(Spacer(1, 30))
        footer_text = f"""
        Ce catalogue contient {products.count()} produits actifs.<br/>
        Pour plus d'informations, contactez {producer.user.email}<br/>
        AgriBusiness - {timezone.now().year}
        """
        story.append(Paragraph(footer_text, normal_style))
        
        # Générer le PDF
        doc.build(story)
        
        # Récupérer le PDF du buffer
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Sauvegarder le fichier
        filename = f"catalog_{producer.user.username}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(settings.MEDIA_ROOT, 'catalogs', filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(pdf_data)
        
        # Notifier le producteur
        NotificationService.create_notification(
            user_id=producer.user.id,
            title="📄 Catalogue PDF généré",
            message=f"Votre catalogue produits a été généré et est disponible au téléchargement.",
            notification_type='INFO'
        )
        
        # Envoyer un email avec le PDF en pièce jointe
        email_sent = EmailService.send_email(
            subject=f"📄 Votre catalogue produits - {producer.farm_name}",
            plain_message=f"Bonjour {producer.user.get_full_name()},\n\n"
                         f"Votre catalogue produits a été généré avec succès.\n"
                         f"Vous trouverez le fichier PDF en pièce jointe.\n\n"
                         f"Cordialement,\nL'équipe AgriBusiness",
            recipient_list=[producer.user.email],
            attachments=[{
                'filename': filename,
                'content': pdf_data,
                'mimetype': 'application/pdf'
            }]
        )
        
        logger.info(f"📄 Catalogue PDF généré pour {producer.farm_name} : {filepath}")
        
        return {
            'success': True,
            'filepath': filepath,
            'filename': filename,
            'products_count': products.count(),
            'email_sent': email_sent,
            'producer_id': producer_id
        }
        
    except ProducerProfile.DoesNotExist:
        logger.error(f"❌ Producteur {producer_id} introuvable")
        return {
            'success': False,
            'message': 'Producteur introuvable',
            'producer_id': producer_id
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur génération PDF producteur {producer_id} : {e}")
        raise self.retry(exc=e)


@shared_task
def update_product_prices_from_external(source: str = 'manual') -> Dict[str, Any]:
    """
    Met à jour les prix depuis une source externe (simulé)
    """
    try:
        # Simuler une API externe
        # En production, vous implémenteriez l'appel API réel ici
        
        if source == 'simulate':
            # Simulation : augmenter tous les prix de 2%
            updated = Product.objects.filter(
                is_active=True,
                can_update_price=True
            ).update(
                price=F('price') * 1.02,
                last_price_update=timezone.now()
            )
            
            logger.info(f"💰 Prix mis à jour pour {updated} produits (simulation +2%)")
            
            return {
                'updated_count': updated,
                'source': source,
                'percentage': 2,
                'timestamp': timezone.now().isoformat()
            }
        
        elif source == 'manual':
            # Pour les mises à jour manuelles, rien à faire
            return {
                'updated_count': 0,
                'source': source,
                'message': 'Mise à jour manuelle requise',
                'timestamp': timezone.now().isoformat()
            }
        
        else:
            logger.warning(f"Source de prix non reconnue : {source}")
            return {
                'updated_count': 0,
                'source': source,
                'message': 'Source non reconnue',
                'timestamp': timezone.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour prix : {e}")
        return {
            'error': str(e),
            'updated_count': 0,
            'source': source
        }


@shared_task
def check_and_deactivate_out_of_stock_products() -> Dict[str, Any]:
    """
    Désactive les produits en rupture de stock depuis longtemps
    """
    try:
        # Produits en rupture depuis plus de 30 jours
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        
        out_of_stock_products = Product.objects.filter(
            is_active=True,
            stock=0,
            last_stock_update__lt=thirty_days_ago,
            auto_deactivate=True
        )
        
        deactivated_count = out_of_stock_products.count()
        
        if deactivated_count > 0:
            # Désactiver les produits
            out_of_stock_products.update(is_active=False)
            
            # Notifier les producteurs concernés
            producers_to_notify = set(
                product.producer.user 
                for product in out_of_stock_products 
                if product.producer
            )
            
            for producer_user in producers_to_notify:
                NotificationService.create_notification(
                    user_id=producer_user.id,
                    title="⚠️ Produits désactivés",
                    message=f"Certains de vos produits ont été désactivés automatiquement car en rupture de stock depuis plus de 30 jours.",
                    notification_type='WARNING',
                    priority=2
                )
            
            logger.warning(f"⚠️ {deactivated_count} produits désactivés (rupture de stock > 30 jours)")
        
        return {
            'deactivated_count': deactivated_count,
            'checked_at': timezone.now().isoformat(),
            'threshold_days': 30
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur désactivation produits : {e}")
        return {
            'error': str(e),
            'deactivated_count': 0
        }


@shared_task
def update_product_recommendations() -> Dict[str, Any]:
    """
    Met à jour les recommandations de produits basées sur l'historique des achats
    """
    try:
        # Logique simple de recommandation
        # En production, vous pourriez utiliser un algorithme plus sophistiqué
        
        # Récupérer les produits fréquemment achetés ensemble
        # (simplifié pour l'exemple)
        
        logger.info("🔄 Mise à jour des recommandations de produits")
        
        # Ici, vous implémenteriez votre logique de recommandation
        # Par exemple, calculer les associations de produits
        
        return {
            'status': 'completed',
            'message': 'Recommandations mises à jour',
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour recommandations : {e}")
        return {
            'error': str(e),
            'status': 'failed'
        }




# from django.template.loader import render_to_string
# from celery import shared_task
# from celery.utils.log import get_task_logger
# from django.core.cache import cache
# from django.utils import timezone
# from apps.products.models import Product, ProducerProfile
# from services.notification_service import NotificationService
# import os



# logger = get_task_logger(__name__)

# @shared_task
# def check_low_stock(threshold=10):
#     """Alerte stock bas (1 fois par 24h par produit)"""
#     low_stock_products = Product.objects.filter(
#         is_active=True,
#         stock__gt=0,
#         stock__lte=threshold
#     ).select_related('producer__user')

#     alerts_sent = 0
#     for product in low_stock_products:
#         cache_key = f"low_stock_alert_{product.id}_{threshold}"
#         if not cache.get(cache_key):
#             NotificationService.notify_low_stock(product, threshold)
#             cache.set(cache_key, True, timeout=86400)  # 24h
#             alerts_sent += 1
#             logger.warning(f"Alerte stock bas : {product.name} (stock: {product.stock})")

#     logger.info(f"{alerts_sent} alerte(s) stock bas envoyée(s)")
#     return f"{alerts_sent} alertes envoyées"


# @shared_task
# def update_product_statistics():
#     """Réinitialise les compteurs journaliers"""
#     updated = Product.objects.update(daily_views=0)
#     logger.info(f"{updated} produits : compteurs journaliers réinitialisés")
#     return "Statistiques réinitialisées"


# @shared_task(bind=True, max_retries=3, retry_backoff=10)
# def generate_product_pdf_catalog(self, producer_id: int):
#     """Génère le catalogue PDF d'un producteur"""
#     from weasyprint import HTML

#     try:
#         producer = ProducerProfile.objects.get(id=producer_id)
#         products = producer.products.filter(is_active=True).order_by('name')

#         if not products.exists():
#             logger.info(f"Aucun produit actif pour le producteur {producer}")
#             return "Aucun produit"

#         html_string = render_to_string('pdf/catalog.html', {
#             'producer': producer,
#             'products': products,
#             'generated_at': timezone.now(),
#         })

#         os.makedirs('catalogs', exist_ok=True)
#         filename = f"catalogs/catalog_{producer.user.username}_{producer_id}_{timezone.now().strftime('%Y%m%d')}.pdf"

#         HTML(string=html_string).write_pdf(target=filename)

#         logger.info(f"PDF généré : {filename}")
#         return filename

#     except Exception as e:
#         logger.error(f"Erreur génération PDF producteur {producer_id} : {e}")
#         raise self.retry(exc=e)


# @shared_task(bind=True, rate_limit='10/m')
# def sync_product_prices(self):
#     """Synchronisation des prix depuis ERP externe (à implémenter)"""
#     try:
#         # Logique API ERP ici
#         logger.info("Synchronisation des prix terminée")
#         return "Prix synchronisés"
#     except Exception as e:
#         logger.error(f"Erreur synchronisation prix : {e}")
     