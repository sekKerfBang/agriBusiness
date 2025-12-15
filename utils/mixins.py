from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from rest_framework import mixins as drf_mixins
from rest_framework.viewsets import GenericViewSet
from functools import partial

# Mixins Django Views
class ProducerRequiredMixin(UserPassesTestMixin):
    """Mixin pour vérifier que l'utilisateur est un producteur validé"""
    def test_func(self):
        return (
            self.request.user.is_authenticated and 
            self.request.user.role == 'PRODUCTEUR' and
            hasattr(self.request.user, 'producer_profile') and
            self.request.user.producer_profile.validated
        )
    
    def get_login_url(self):
        return '/login/'

class ClientRequiredMixin(UserPassesTestMixin):
    """Mixin pour les clients"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'CLIENT'

# Mixins DRF
class BaseAPIMixin(drf_mixins.ListModelMixin,
                   drf_mixins.CreateModelMixin,
                   drf_mixins.RetrieveModelMixin,
                   drf_mixins.UpdateModelMixin,
                   drf_mixins.DestroyModelMixin,
                   GenericViewSet):
    """Mixin de base pour toutes les APIs CRUD"""
    pass

# Partial functions pour créer des viewsets rapides
StandardCRUDViewSet = partial(
    type,
    'StandardCRUDViewSet',
    (BaseAPIMixin,),
    {}
)

class CacheResponseMixin:
    """Mixin pour cacher les réponses API"""
    cache_timeout = 60 * 5  # 5 minutes par défaut
    
    def dispatch(self, request, *args, **kwargs):
        from django.core.cache import cache
        from django.http import HttpResponse
        
        cache_key = f"api_{request.path}_{request.user.id}"
        response = cache.get(cache_key)
        
        if response:
            return response
        
        response = super().dispatch(request, *args, **kwargs)
        
        if response.status_code == 200:
            cache.set(cache_key, response, self.cache_timeout)
        
        return response


# from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
# from functools import partial
# from rest_framework import mixins as drf_mixins
# from rest_framework.viewsets import GenericViewSet

# # Partial pour créer des mixins rapidement
# create_permission_mixin = partial(
#     UserPassesTestMixin,
#     login_url='/login/'
# )

# class ProducerRequiredMixin(create_permission_mixin):
#     """Mixin pour vérifier que l'utilisateur est un producteur"""
#     def test_func(self):
#         return self.request.user.is_authenticated and self.request.user.role == 'PRODUCTEUR'

# class APIMixin(drf_mixins.ListModelMixin,
#                drf_mixins.CreateModelMixin,
#                drf_mixins.RetrieveModelMixin,
#                GenericViewSet):
#     """Mixin partial pour API standard CRUD"""
#     pass

# # Partial pour créer des ViewSets rapides
# StandardViewSet = partial(
#     type,
#     'StandardViewSet',
#     (APIMixin,),
#     {}
# )