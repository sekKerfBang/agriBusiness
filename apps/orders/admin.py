from django.contrib import admin
from .models import Order, OrderItem, Cart, CartItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal']
    raw_id_fields = ['product']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'client', 'status', 'total_amount', 
        'items_count', 'payment_status', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'client__username', 'client__email']
    raw_id_fields = ['client']
    readonly_fields = ['order_number', 'total_amount', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    actions = ['mark_as_shipped', 'mark_as_delivered']
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='SHIPPED')
    mark_as_shipped.short_description = "Marquer comme expédié"
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='DELIVERED')
    mark_as_delivered.short_description = "Marquer comme livré"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'items_count', 'updated_at']
    raw_id_fields = ['user']
    search_fields = ['user__username']
    
    def items_count(self, obj):
        return obj.items.count()