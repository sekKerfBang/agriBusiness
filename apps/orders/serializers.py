from rest_framework import serializers
from .models import Order, OrderItem, Cart, CartItem

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_image', 'quantity', 'unit_price', 'subtotal']
        read_only_fields = ['subtotal']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    can_be_cancelled = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['order_number', 'client', 'total_amount', 'payment_intent_id']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = serializers.ListField(write_only=True)
    shipping_address = serializers.CharField(required=True)
    
    class Meta:
        model = Order
        fields = ['shipping_address', 'items']
    
    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Le panier ne peut pas être vide")
        
        for item in items:
            if item.get('quantity', 0) <= 0:
                raise serializers.ValidationError("Quantité invalide")
        
        return items


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'product_price', 'quantity']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total', 'updated_at']
        read_only_fields = ['user']
    
    def get_total(self, obj):
        return sum(item.quantity * item.product.price for item in obj.items.all())