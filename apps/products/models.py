from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.utilisateur.models import  ProducerProfile 
from django.contrib import admin

class Category(models.Model):
    """Catégories de produits (Fruits, Légumes, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, help_text="Font Awesome icon (ex: fa-apple)")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = 'products'  # Fix pour matcher INSTALLED_APPS (évite conflits)
        ordering = ['order', 'name']
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    """Produit agricole"""
    UNIT_CHOICES = [
        ('kg', 'Kilogramme'),
        ('piece', 'Pièce'),
        ('botte', 'Botte'),
        ('litre', 'Litre'),
        ('sac', 'Sac'),
    ]
    
    producer = models.ForeignKey(
        ProducerProfile,  # ← FIX E300/E307 : String ref vers le bon app/model (pas 'users' !)
        on_delete=models.CASCADE, 
        related_name='products'
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.ImageField(upload_to='products/%Y/%m/', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Stats
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = 'products'  # Fix pour matcher INSTALLED_APPS
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['price']),
        ]

    @property
    @admin.display(boolean=True, description='Disponible')
    def is_available(self):
        """Retourne True si le produit est actif ET en stock"""
        return self.is_active and self.stock > 0
    
    def __str__(self):
        return f"{self.name} - {self.producer.user.username}"  # Assure-toi que 'farm_name' existe dans ProducerProfile

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def stock_status(self):
        if self.stock == 0:
            return 'out_of_stock'
        elif self.stock < 10:
            return 'low_stock'
        return 'in_stock'


# class ProducerProfile(models.Model):
#     """Profil producteur"""
#     user = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='producer_profile')
#     farm_name = models.CharField(max_length=255)
#     bio = models.TextField(blank=True)
#     address = models.TextField()
#     phone = models.CharField(max_length=20)
#     website = models.URLField(blank=True)
#     is_verified = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     # ← FIX E108/E116 : Ajoute les champs référencés dans admin
#     siret = models.CharField(max_length=14, blank=True, unique=True, verbose_name=_("Numéro SIRET"))  # Ajouté pour list_display
#     is_organic = models.BooleanField(default=False, verbose_name=_("Certification bio"))  # Ajouté pour list_filter/display
#     validated = models.BooleanField(default=False, verbose_name=_("Validé par admin"))  # Ajouté pour list_filter/display

#     class Meta:
#         app_label = 'apps.products'  # Si tu le gardes ici ; sinon déplace en 'apps.utilisateur'
#         ordering = ['farm_name']

#     def __str__(self):
#         return self.farm_name