# orders/admin.py (ou marketplace/admin.py)

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Order, OrderItem, Cart, CartItem


# ==================== INLINE POUR ORDERITEM ====================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'quantity', 'unit_price', 'subtotal')
    readonly_fields = ('subtotal',)
    raw_id_fields = ('product',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


# ==================== ADMIN ORDER ====================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number_link', 'client_link', 'status_badge', 'total_amount',
        'items_count', 'payment_status', 'created_at_formatted'
    ]
    list_filter = [
        'status', 'payment_status', 'created_at', 'client__role'
    ]
    search_fields = [
        'order_number', 'client__username', 'client__email',
        'client__first_name', 'client__last_name'
    ]
    date_hierarchy = 'created_at'
    raw_id_fields = ['client']
    readonly_fields = [
        'order_number', 'total_amount', 'created_at', 'updated_at',
        'payment_intent_id'
    ]
    fieldsets = (
        ('Informations générales', {
            'fields': ('order_number', 'client', 'status', 'payment_status', 'payment_intent_id')
        }),
        ('Montant & Dates', {
            'fields': ('total_amount', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Livraison', {
            'fields': ('shipping_address', 'notes'),
        }),
        ('Suivi', {
            'fields': ('tracking_number',),
            'classes': ('collapse',)
        }),
    )
    inlines = [OrderItemInline]

    # Actions personnalisées
    actions = ['mark_as_preparing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']

    def mark_as_preparing(self, request, queryset):
        updated = queryset.update(status=Order.Status.PREPARING)
        self.message_user(request, f"{updated} commande(s) marquée(s) en préparation.")
    mark_as_preparing.short_description = "FMarquer comme en préparation"

    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status=Order.Status.SHIPPED)
        self.message_user(request, f"{updated} commande(s) marquée(s) comme expédiée(s).")
    mark_as_shipped.short_description = "Marquer comme expédiée(s)"

    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status=Order.Status.DELIVERED)
        self.message_user(request, f"{updated} commande(s) marquée(s) comme livrée(s).")
    mark_as_delivered.short_description = "Marquer comme livrée(s)"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.filter(status__in=[Order.Status.PENDING, Order.Status.CONFIRMED]).update(status=Order.Status.CANCELLED)
        self.message_user(request, f"{updated} commande(s) annulée(s).")
    mark_as_cancelled.short_description = "Annuler les commandes sélectionnées"

    # Colonnes personnalisées
    def order_number_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.pk])
        return format_html('<a href="{}"><strong>{}</strong></a>', url, obj.order_number)
    order_number_link.short_description = "Numéro de commande"
    order_number_link.admin_order_field = 'order_number'

    def client_link(self, obj):
        url = reverse('admin:utilisateur_utilisateur_change', args=[obj.client.pk])
        return format_html('<a href="{}">{}</a>', url, obj.client.get_full_name() or obj.client.username)
    client_link.short_description = "Client"
    client_link.admin_order_field = 'client__username'

    def status_badge(self, obj):
        colors = {
            Order.Status.PENDING: 'warning',
            Order.Status.CONFIRMED: 'info',
            Order.Status.PREPARING: 'secondary',
            Order.Status.SHIPPED: 'primary',
            Order.Status.DELIVERED: 'success',
            Order.Status.CANCELLED: 'danger',
            Order.Status.REFUNDED: 'dark',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{} text-white px-3 py-2 rounded-pill">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Statut"

    def created_at_formatted(self, obj):
        return timezone.localtime(obj.created_at).strftime('%d/%m/%Y %H:%M')
    created_at_formatted.short_description = "Date"
    created_at_formatted.admin_order_field = 'created_at'

    def items_count(self, obj):
        return obj.items_count
    items_count.short_description = "Articles"


# ==================== ADMIN CART ====================
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ('product', 'quantity', 'get_subtotal')
    readonly_fields = ('get_subtotal',)
    raw_id_fields = ('product',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user_link', 'items_count', 'total_amount', 'updated_at_formatted']
    list_filter = ['updated_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    date_hierarchy = 'updated_at'
    raw_id_fields = ['user']
    inlines = [CartItemInline]
    readonly_fields = ['created_at', 'updated_at']

    def user_link(self, obj):
        url = reverse('admin:utilisateur_utilisateur_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name() or obj.user.username)
    user_link.short_description = "Utilisateur"
    user_link.admin_order_field = 'user__username'

    def total_amount(self, obj):
        return f"{obj.get_total_amount():.2f} €"
    total_amount.short_description = "Total panier"

    def updated_at_formatted(self, obj):
        return timezone.localtime(obj.updated_at).strftime('%d/%m/%Y %H:%M')
    updated_at_formatted.short_description = "Mis à jour"
    updated_at_formatted.admin_order_field = 'updated_at'

    def items_count(self, obj):
        return obj.items_count
    items_count.short_description = "Articles"


# ==================== ADMIN CARTITEM (optionnel, pour debug) ====================
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'get_subtotal']
    list_filter = ['cart__user']
    search_fields = ['product__name', 'cart__user__username']
    raw_id_fields = ['cart', 'product']



# from django.contrib import admin
# from .models import Order, OrderItem, Cart, CartItem

# class OrderItemInline(admin.TabularInline):
#     model = OrderItem
#     extra = 0
#     readonly_fields = ['subtotal']
#     raw_id_fields = ['product']


# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = [
#         'order_number', 'client', 'status', 'total_amount', 
#         'items_count', 'payment_status', 'created_at'
#     ]
#     list_filter = ['status', 'payment_status', 'created_at']
#     search_fields = ['order_number', 'client__username', 'client__email']
#     raw_id_fields = ['client']
#     readonly_fields = ['order_number', 'total_amount', 'created_at', 'updated_at']
#     inlines = [OrderItemInline]
    
#     actions = ['mark_as_shipped', 'mark_as_delivered']
    
#     def mark_as_shipped(self, request, queryset):
#         queryset.update(status='SHIPPED')
#     mark_as_shipped.short_description = "Marquer comme expédié"
    
#     def mark_as_delivered(self, request, queryset):
#         queryset.update(status='DELIVERED')
#     mark_as_delivered.short_description = "Marquer comme livré"


# @admin.register(Cart)
# class CartAdmin(admin.ModelAdmin):
#     list_display = ['user', 'items_count', 'updated_at']
#     raw_id_fields = ['user']
#     search_fields = ['user__username']
    
#     def items_count(self, obj):
#         return obj.items.count()