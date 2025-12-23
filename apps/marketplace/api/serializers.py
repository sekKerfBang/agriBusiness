from rest_framework import serializers
from apps.products.models import Product, Category
from apps.orders.models import  Order, OrderItem, Cart, CartItem
from apps.utilisateur.models import ProducerProfile  

# ========================
# Catégorie
# ========================
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'icon', 'description']

# ========================
# Producteur (pour détail produit)
# ========================
class ProducerMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProducerProfile
        fields = ['id', 'farm_name', 'description', 'avatar']

# ========================
# Produit
# ========================
class ProductSerializer(serializers.ModelSerializer):
    producer_name = serializers.CharField(source='producer.farm_name', read_only=True)
    producer_id = serializers.IntegerField(source='producer.id', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    stock_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'unit', 'stock',
            'image', 'is_active', 'is_deleted', 'view_count',
            'producer_name', 'producer_id', 'category_name',
            'stock_status', 'created_at'
        ]
        read_only_fields = ['created_at', 'producer_name', 'producer_id', 'category_name']
    
    def get_stock_status(self, obj):
        if obj.stock == 0:
            return "Rupture"
        elif obj.stock < 10:
            return "Stock faible"
        return "Disponible"
    
    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Le stock ne peut pas être négatif")
        return value
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le prix doit être positif")
        return value

# ========================
# Article de commande
# ========================
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_image', 'product_price', 'quantity', 'subtotal']
        read_only_fields = ['subtotal']

# ========================
# Commande
# ========================
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(source='items.count', read_only=True)
    client_name = serializers.CharField(source='client.get_full_name', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'client', 'client_name', 'total_amount',
            'status', 'get_status_display', 'created_at', 'shipping_address',
            'items', 'items_count'
        ]
        read_only_fields = ['order_number', 'client', 'total_amount', 'created_at']

# ========================
# Création de commande (mobile)
# ========================
class OrderCreateSerializer(serializers.ModelSerializer):
    items = serializers.ListField(child=serializers.DictField(), write_only=True)
    
    class Meta:
        model = Order
        fields = ['shipping_address', 'items']
    
    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Le panier ne peut pas être vide")
        for item in items:
            if item.get('quantity', 0) <= 0:
                raise serializers.ValidationError("Quantité invalide")
            if not item.get('product_id'):
                raise serializers.ValidationError("product_id manquant")
        return items
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(
            client=self.context['request'].user,
            shipping_address=validated_data['shipping_address'],
            status='PENDING'
        )
        
        total = 0
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                unit_price=product.price
            )
            total += product.price * item_data['quantity']
        
        order.total_amount = total
        order.save()
        return order

# ========================
# Panier
# ========================
class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['product', 'product_name', 'product_image', 'product_price', 'quantity']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    items_count = serializers.IntegerField(source='items.count', read_only=True)
    
    class Meta:
        model = Cart
        fields = ['items', 'total', 'items_count', 'updated_at']
    
    def get_total(self, obj):
        return sum(item.quantity * item.product.price for item in obj.items.all())

# from rest_framework import serializers
# from apps.products.models  import Product, Category

# class CategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Category
#         fields = ['id', 'name', 'icon', 'description']


# class ProductSerializer(serializers.ModelSerializer):
#     producer_name = serializers.CharField(source='producer.farm_name', read_only=True)
#     producer_id = serializers.IntegerField(source='producer.id', read_only=True)
#     category_name = serializers.CharField(source='category.name', read_only=True)
#     stock_status = serializers.CharField(read_only=True)
    
#     class Meta:
#         model = Product
#         fields = '__all__'
#         read_only_fields = ['view_count', 'created_at', 'updated_at']
    
#     def validate_stock(self, value):
#         if value < 0:
#             raise serializers.ValidationError("Le stock ne peut pas être négatif")
#         return value
    
#     def validate_price(self, value):
#         if value <= 0:
#             raise serializers.ValidationError("Le prix doit être positif")
#         return value