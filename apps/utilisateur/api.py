from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from .models import ProducerProfile
from .serializers import UtilisateurSerializer, ProducerProfileSerializer, UtilisateurRegistrationSerializer
from services.email_service import AsyncEmailService

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UtilisateurSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return UtilisateurRegistrationSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Récupère les infos de l'utilisateur connecté"""
        return Response(UtilisateurSerializer(request.user).data)

    @action(detail=True, methods=['post'], url_path='validate-producer')
    def validate_producer(self, request, pk=None):
        """Valide un compte producteur (admin only)"""
        if not request.user.is_staff:
            return Response({'error': 'Accès refusé'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user = self.get_object()
            if user.role != 'PRODUCTEUR':
                return Response({'error': 'Utilisateur non producteur'}, status=status.HTTP_400_BAD_REQUEST)
            
            profile = user.producer_profile
            profile.validated = True
            profile.save()
            
            # Email async
            AsyncEmailService.send_welcome_email(user)
            
            return Response({'status': 'Producteur validé'})
        except ProducerProfile.DoesNotExist:
            return Response({'error': 'Profil producteur introuvable'}, status=status.HTTP_404_NOT_FOUND)


class ProducerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProducerProfile.objects.filter(validated=True).select_related('user')
    serializer_class = ProducerProfileSerializer
    permission_classes = [AllowAny]
    search_fields = ['farm_name', 'description']
    filterset_fields = ['is_organic']

    @action(detail=True, methods=['get'], url_path='products')
    def get_products(self, request, pk=None):
        """Récupère les produits d'un producteur"""
        producer = self.get_object()
        products = producer.products.filter(is_active=True)
        from apps.products.serializers import ProductSerializer
        return Response(ProductSerializer(products, many=True).data)