from django.contrib import admin
from .models import Product, Category
from django.utils.translation import gettext_lazy as _ 


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'producer', 'price', 'stock', 'get_is_available']  # ← FIX E108 : Utilise method pour property (get_is_available)
    list_filter = ['category', 'created_at', 'producer__is_organic']  # ← FIX E116 : is_organic est maintenant Field sur ProducerProfile
    search_fields = ['name', 'description']
    raw_id_fields = ['producer']

    def get_is_available(self, obj):
        return obj.is_available  # ← FIX : Method pour display property comme bool (admin le gère avec icon true/false)
    get_is_available.boolean = True  # Affiche oui/non icon
    #cette ligne est optionnelle mais améliore la lisibilité dans l'admin
    get_is_available.short_description = _('Disponible')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

# @admin.register(ProducerProfile)
# class ProductProfileAdmin(admin.ModelAdmin):
#     list_display = ['farm_name', 'user', 'siret', 'is_organic', 'validated']  # ← FIX E108 : Champs ajoutés dans model
#     list_filter = ['is_organic', 'validated']  # ← FIX E116 : Maintenant Fields (BooleanField)
#     search_fields = ['farm_name', 'user__username', 'siret']
#     raw_id_fields = ['user']