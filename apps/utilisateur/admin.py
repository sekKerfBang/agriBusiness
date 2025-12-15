from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, ProducerProfile  # Si ProducerProfile ici, register ici ; sinon supprime

@admin.register(Utilisateur)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'phone', 'is_active', 'created_at']  # ← FIX E108 : created_at ajouté dans model
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'phone']
    ordering = ['-created_at']  # ← FIX E033 : created_at est maintenant Field
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('role', 'phone', 'address', 'avatar', 'email_verified')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('email', 'role', 'phone')
        }),
    )

# Si ProducerProfile est dans utilisateur/models.py
@admin.register(ProducerProfile)
class ProducerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_organic', 'certifications', 'description']
    list_filter = ['is_organic']
    search_fields = ['user__username', 'description']