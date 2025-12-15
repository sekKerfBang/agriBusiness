from django.db.models import Q, Count, Avg
from django.db import transaction
from .models import Product, Category
from services.notification_service import NotificationService

class ProductService:
    """Service layer pour la gestion des produits"""
    
    @staticmethod
    def search_products(query, category=None, producer=None, min_price=None, max_price=None):
        """Recherche avancée de produits"""
        products = Product.objects.filter(is_active=True)
        
        if query:
            products = products.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(producer__farm_name__icontains=query)
            )
        
        if category:
            products = products.filter(category_id=category)
        
        if producer:
            products = products.filter(producer_id=producer)
        
        if min_price:
            products = products.filter(price__gte=min_price)
        
        if max_price:
            products = products.filter(price__lte=max_price)
        
        return products.distinct()
    
    @staticmethod
    def get_recommendations(product_id, limit=5):
        """Produit des recommandations basées sur la catégorie"""
        product = Product.objects.get(id=product_id)
        recommendations = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product_id)[:limit]
        return recommendations
    
    @staticmethod
    @transaction.atomic
    def bulk_update_stock(products_data):
        """Mise à jour massive du stock"""
        updated = []
        for item in products_data:
            product = Product.objects.select_for_update().get(id=item['id'])
            old_stock = product.stock
            product.stock = item['stock']
            product.save()
            updated.append(product)
            
            # Notification si besoin
            if product.stock < 10 and old_stock >= 10:
                NotificationService.notify_low_stock(product)
        
        return updated
    
    @staticmethod
    def get_producer_catalog(producer_id):
        """Récupère le catalogue complet d'un producteur"""
        products = Product.objects.filter(
            producer_id=producer_id,
            is_active=True
        ).select_related('category')
        
        return {
            'total_products': products.count(),
            'categories': products.values('category__name').annotate(count=Count('id')),
            'products': products,
            'stock_alerts': products.filter(stock__lt=10).count()
        }