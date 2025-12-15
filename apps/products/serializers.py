from rest_framework import serializers
from .models import Product, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'icon', 'description']


class ProductSerializer(serializers.ModelSerializer):
    producer_name = serializers.CharField(source='producer.farm_name', read_only=True)
    producer_id = serializers.IntegerField(source='producer.id', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    stock_status = serializers.CharField(read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['view_count', 'created_at', 'updated_at']
    
    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Le stock ne peut pas être négatif")
        return value
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le prix doit être positif")
        return value