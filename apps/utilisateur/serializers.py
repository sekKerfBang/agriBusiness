from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ProducerProfile

User = get_user_model()

class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'phone', 'address', 'avatar', 'email_verified']
        read_only_fields = ['id', 'email_verified']


class ProducerProfileSerializer(serializers.ModelSerializer):
    user = UtilisateurSerializer(read_only=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = ProducerProfile
        fields = '__all__'

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class UtilisateurRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    farm_name = serializers.CharField(write_only=True, required=False)
    siret = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 
                 'role', 'phone', 'farm_name', 'siret']

    def validate(self, data):
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas"})
        
        if data.get('role') == 'PRODUCTEUR':
            if not data.get('farm_name') or not data.get('siret'):
                raise serializers.ValidationError({"role": "Producteur requiert farm_name et siret"})
        
        return data

    def create(self, validated_data):
        farm_name = validated_data.pop('farm_name', None)
        siret = validated_data.pop('siret', None)
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'CLIENT'),
            phone=validated_data.get('phone', '')
        )
        
        if user.role == 'PRODUCTEUR':
            ProducerProfile.objects.create(
                user=user,
                farm_name=farm_name,
                siret=siret,
                description="Nouveau producteur"
            )
        
        return user