from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Utilisateur(AbstractUser):
    class Role(models.TextChoices):
        CLIENT = 'CLIENT', _('Client (Agriculteur/Acheteur)')
        ENTREPRISE = 'ENTREPRISE', _('Entreprise (Producteur/Fournisseur)')

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    location = models.CharField(max_length=255, blank=True, help_text="Ex: Coordonnées GPS de la ferme")
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # ← FIX : Ajouté pour ordering/list_display
    last_password_change = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Dernier changement de mot de passe"
    )
    image = models.ImageField(upload_to='user_profiles/', null=True, blank=True, verbose_name=_("Image de profil"))

    class Meta:
        app_label = 'utilisateur'  
        verbose_name = _('Utilisateur')
        verbose_name_plural = _('Utilisateurs')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    @property
    def is_entreprise(self):
        return self.role == self.Role.ENTREPRISE
    
    def set_password(self, raw_password):
        super().set_password(raw_password)
        self.last_password_change = timezone.now()
    
    
class ProducerProfile(models.Model):  # Si ici
    user = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='producer_profile'
    )
    is_organic = models.BooleanField(default=False, verbose_name=_("Certification bio"))  # ← FIX : Ajouté pour filter
    description = models.TextField(blank=True, verbose_name=_("Description (spécialités agricoles)"))
    certifications = models.CharField(max_length=255, blank=True, verbose_name=_("Certifications (ex: AB, HVE)"))
    validated = models.BooleanField(default=False, verbose_name=_("Validé par admin"))  # ← FIX : Ajouté pour filter 
    image = models.ImageField(upload_to='producer_profiles/', null=True, blank=True, verbose_name=_("Image de profil"))
    class Meta:
        app_label = 'utilisateur'
        verbose_name = _('Profil Producteur')
        verbose_name_plural = _('Profils Producteurs')

    def __str__(self):
        return f"Profil de {self.user.username}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('NEW_ORDER', 'Nouvelle commande'),
        ('LOW_STOCK', 'Stock bas'),
        ('ORDER_UPDATE', 'Mise à jour commande'),
        ('MESSAGE', 'Nouveau message'),
        ('INFO', 'Information'),
    ]

    user = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_order = models.ForeignKey('orders.Order', null=True, blank=True, on_delete=models.SET_NULL)
    related_product = models.ForeignKey('products.Product', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"