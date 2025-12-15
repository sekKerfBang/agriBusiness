from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Order, OrderItem, Cart, CartItem
from .serializers import OrderSerializer, OrderCreateSerializer, CartSerializer
from services.payment_service import PaymentService
from tasks.email_tasks import send_order_confirmation_task

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role == 'CLIENT':
            return Order.objects.filter(client=self.request.user).prefetch_related('items')
        return Order.objects.filter(
            items__product__producer__user=self.request.user
        ).distinct().prefetch_related('items')

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        with transaction.atomic():
            order = serializer.save(client=self.request.user)
            
            # Créer les items
            items_data = self.request.data.get('items', [])
            for item_data in items_data:
                product = get_object_or_404(OrderItem, product_id=item_data['product'])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item_data['quantity'],
                    unit_price=product.price
                )
                # Mettre à jour le stock
                product.stock -= item_data['quantity']
                product.save()
            
            # Email async
            send_order_confirmation_task.delay(order.id)
            
            return order

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Annule une commande"""
        order = self.get_object()
        
        if order.client != request.user and not request.user.is_staff:
            return Response({'error': 'Accès refusé'}, status=status.HTTP_403_FORBIDDEN)
        
        if not order.can_be_cancelled:
            return Response({'error': 'Commande ne peut pas être annulée'}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = 'CANCELLED'
        order.save()
        
        # Remettre le stock
        for item in order.items.all():
            item.product.stock += item.quantity
            item.product.save()
        
        return Response({'status': 'Commande annulée'})

    @action(detail=True, methods=['post'])
    def initiate_payment(self, request, pk=None):
        """Initie le paiement Stripe"""
        order = self.get_object()
        
        if order.client != request.user:
            return Response({'error': 'Accès refusé'}, status=status.HTTP_403_FORBIDDEN)
        
        if order.status != 'PENDING':
            return Response({'error': 'Paiement déjà traité'}, status=status.HTTP_400_BAD_REQUEST)
        
        payment_intent = PaymentService.create_payment_intent(
            amount=order.total_amount,
            currency='eur',
            metadata={'order_id': order.id}
        )
        
        order.payment_intent_id = payment_intent.id
        order.save()
        
        return Response({
            'client_secret': payment_intent.client_secret,
            'payment_intent_id': payment_intent.id
        })


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).prefetch_related('items')

    def perform_create(self, serializer):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Ajoute un produit au panier"""
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        
        from apps.products.models import Product
        product = get_object_or_404(Product, id=product_id)
        
        if product.stock < quantity:
            return Response({'error': 'Stock insuffisant'}, status=status.HTTP_400_BAD_REQUEST)
        
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            item.quantity += quantity
            item.save()
        
        return Response(CartSerializer(cart).data)

    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        """Retire un produit du panier"""
        cart = self.get_object()
        product_id = request.data.get('product_id')
        
        CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        
        return Response(CartSerializer(cart).data)

    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        """Vide le panier"""
        cart = self.get_object()
        cart.items.all().delete()
        
        return Response({'status': 'Panier vidé'})