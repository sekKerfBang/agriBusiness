from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, ProducerProfile, Notification

@admin.register(Utilisateur)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'phone', 'is_active', 'created_at']    
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'phone']
    ordering = ['-created_at'] 
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('role', 'phone', 'image')
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
    fieldsets = (
        (None, {
            'fields': ('user', 'is_organic', 'certifications', 'description', 'validated', 'image')
        }),
    )

@admin.register(Notification)
class NotificationsAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'title', 'is_read', 'created_at']