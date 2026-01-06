from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from apps.products.models import Product
from django.utils import timezone
from apps.utilisateur.models import Utilisateur

User = Utilisateur

class Order(models.Model):
    class Status(models.TextChoices):  # ← Upgradé : TextChoices pour Django 6.0
        PENDING = 'PENDING', _('En attente de paiement')
        CONFIRMED = 'CONFIRMED', _('Commande confirmée')
        PREPARING = 'PREPARING', _('En préparation')
        SHIPPED = 'SHIPPED', _('Expédiée')
        DELIVERED = 'DELIVERED', _('Livrée')
        CANCELLED = 'CANCELLED', _('Annulée')
        REFUNDED = 'REFUNDED', _('Remboursée')

    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        limit_choices_to={'role': 'CLIENT'}  # ← Filtre rôle pour cohérence UML
    )
    order_number = models.CharField(max_length=50, unique=True, db_index=True, verbose_name=_('Numéro de commande'))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name=_('Statut'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Montant total'))
    shipping_address = models.TextField(blank=True, verbose_name=_('Adresse de livraison'))
    tracking_number = models.CharField(max_length=100, blank=True, verbose_name=_('Numéro de suivi'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Créé le'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Mis à jour le'))
    
    # Données de paiement (ex: Stripe pour business agro)
    payment_intent_id = models.CharField(max_length=255, blank=True, verbose_name=_('ID intention paiement'))
    payment_status = models.CharField(max_length=20, default='pending', verbose_name=_('Statut paiement'))

    class Meta:
        app_label = 'orders'  # ← Fix clé : full path pour matcher INSTALLED_APPS
        verbose_name = _('Commande')
        verbose_name_plural = _('Commandes')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['status', 'created_at']),  # Pour dashboards récents
        ]

    def __str__(self):
        return f"Commande #{self.order_number} - {self.client.username}"
    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # 1️⃣ Premier save pour obtenir le PK
        if is_new:
            super().save(*args, **kwargs)

        # 2️⃣ Génération du numéro UNIQUE basé sur le PK
        if not self.order_number:
            self.order_number = self.generate_order_number()

        # 3️⃣ Calcul du total
        self.total_amount = self.get_total_amount()

        # 4️⃣ Save final
        super().save(update_fields=['order_number', 'total_amount'] if not is_new else None)

    # def save(self, *args, **kwargs):
    #     if not self.order_number:
    #         self.order_number = self.generate_order_number()
    #     self.total_amount = self.get_total_amount()    
    #     super().save(*args, **kwargs)

    def generate_order_number(self):
        """Génère un numéro unique AGR-YYYYMMDD-USERID-PK"""
        """AGR-YYYYMMDD-PK"""
        date_str = timezone.now().strftime('%Y%m%d')
        return f"AGR-{date_str}-{self.pk:06d}"
        # from datetime import datetime
        # pk_str = str(self.pk) if self.pk else 'NEW'
        # return f"AGR-{datetime.now().strftime('%Y%m%d')}-{self.client.id:06d}-{pk_str[:6]}"  # Padding pour unicité

    def get_total_amount(self):
        """Calcule total depuis OrderItem (auto si pas set)"""
        if self.pk:  # Seulement si l'objet existe déjà en BDD (pour items.all())
            return sum(item.subtotal for item in self.items.all()) or 0
        return 0 

    @property
    def items_count(self):
        return self.items.count()

    @property
    def can_be_cancelled(self):
        return self.status in [self.Status.PENDING, self.Status.CONFIRMED]

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_('Produit'), related_name='order_items')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Quantité'))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Prix unitaire'))
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Sous-total'))

    class Meta:
        app_label = 'orders'  # ← Fix
        verbose_name = _('Élément de commande')
        verbose_name_plural = _('Éléments de commande')
        unique_together = ['order', 'product']

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        self.unit_price = self.product.price  # Sync avec prix actuel du produit
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class Cart(models.Model):
    """Panier persistant pour clients connectés"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        limit_choices_to={'role': 'CLIENT'}
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Créé le'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Mis à jour le'))

    class Meta:
        app_label = 'orders'  # ← Fix
        verbose_name = _('Panier')
        verbose_name_plural = _('Paniers')
        ordering = ['-created_at']

    def __str__(self):
        return f"Panier de {self.user.username}"

    def get_total_amount(self):
        return sum(item.get_subtotal() for item in self.items.all()) or 0

    @property
    def items_count(self):
        return self.items.count()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_('Produit'))
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Quantité'))

    class Meta:
        app_label = 'orders'  # ← Fix
        verbose_name = _('Élément de panier')
        verbose_name_plural = _('Éléments de panier')
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def get_subtotal(self):
        return self.quantity * self.product.price

    def save(self, *args, **kwargs):
        if self.quantity <= 0:
            self.delete()
            return
        super().save(*args, **kwargs)
