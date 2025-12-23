# marketplace/api/views.py
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from apps.products.models import Product
from apps.orders.models import  Order, OrderItem, Cart, CartItem
from marketplace.api.serializers import ProductSerializer, OrderSerializer, CartSerializer

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True).select_related('category', 'producer')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(client=self.request.user)

class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def current(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add(self, request):
        # Logique d'ajout au panier (réutilise ta fonction add_to_cart si possible)
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        # ... implémentation
        return Response({"status": "added"})



# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated, AllowAny
# from django.db.models import Q, Count
# from ..models import Product, Category
# from .serializers import ProductSerializer, CategorySerializer
# from services.notification_service import NotificationService

# class ProductViewSet(viewsets.ModelViewSet):
#     queryset = Product.objects.filter(is_active=True).select_related(
#         'producer', 'category', 'producer__user'
#     )
#     serializer_class = ProductSerializer
#     permission_classes = [AllowAny]
#     filterset_fields = ['category', 'producer', 'unit']
#     search_fields = ['name', 'description', 'producer__farm_name']
#     ordering_fields = ['price', 'created_at', 'view_count']
    
#     def get_permissions(self):
#         if self.action in ['create', 'update', 'partial_update', 'destroy']:
#             return [IsAuthenticated()]
#         return super().get_permissions()

#     def perform_create(self, serializer):
#         if not hasattr(self.request.user, 'producer_profile'):
#             raise PermissionError("Vous devez être un producteur")
#         serializer.save(producer=self.request.user.producer_profile)

#     @action(detail=True, methods=['post'])
#     def increment_views(self, request, pk=None):
#         """Incrémente le compteur de vues"""
#         product = self.get_object()
#         Product.objects.filter(pk=pk).update(view_count=models.F('view_count') + 1)
#         return Response({'status': 'view counted'})

#     @action(detail=True, methods=['post'])
#     def update_stock(self, request, pk=None):
#         """Met à jour le stock (producteur uniquement)"""
#         product = self.get_object()
#         if product.producer.user != request.user:
#             return Response({'error': 'Accès refusé'}, status=status.HTTP_403_FORBIDDEN)
        
#         new_stock = request.data.get('stock')
#         old_stock = product.stock
        
#         product.stock = new_stock
#         product.save()
        
#         # Notification si stock bas
#         if float(new_stock) < 10:
#             NotificationService.notify_low_stock(product)
        
#         return Response({'status': 'stock updated', 'new_stock': new_stock})


# class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = Category.objects.filter(is_active=True)
#     serializer_class = CategorySerializer
#     permission_classes = [AllowAny]
    
#     @action(detail=True, methods=['get'])
#     def products(self, request, pk=None):
#         """Récupère tous les produits d'une catégorie"""
#         category = self.get_object()
#         products = category.products.filter(is_active=True)
#         page = self.paginate_queryset(products)
#         serializer = ProductSerializer(page, many=True)
#         return self.get_paginated_response(serializer.data)