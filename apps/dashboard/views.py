from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from apps.products.models import Product
from apps.orders.models import Order, OrderItem


class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal du producteur"""
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if not user.is_entreprise or not hasattr(user, 'producer_profile'):
            context['error'] = "Vous n'avez pas accès au dashboard producteur. <a href='/marketplace/'>Retour au marché</a>."
            # Defaults vides pour éviter erreurs
            context['stats'] = {'total_products': 0, 'active_products': 0, 'total_orders': 0, 'revenue': 0, 'pending_orders': 0, 'low_stock': 0}
            context['recent_orders'] = []
            context['stock_alerts'] = []
            return context

        producer = user.producer_profile
        products_qs = Product.objects.filter(producer=producer)
        orders_qs = Order.objects.filter(items__product__in=products_qs).distinct()

        # Stats (comme ton code)
        context['stats'] = {
            'total_products': products_qs.count(),
            'active_products': products_qs.filter(is_active=True).count(),
            'total_orders': orders_qs.count(),
            'pending_orders': orders_qs.filter(status='PENDING').count(),
            'revenue': orders_qs.filter(status='DELIVERED').aggregate(total=Sum('total_amount'))['total'] or 0,
            'low_stock': products_qs.filter(stock__lt=10).count(),
        }

        context['recent_orders'] = orders_qs.order_by('-created_at')[:6]
        context['stock_alerts'] = products_qs.filter(stock__lt=10).order_by('stock')[:6]

        return context

##  Product File 

class ProductManagementView(LoginRequiredMixin, TemplateView):
    """Gestion des produits du producteur"""
    template_name = 'dashboard/products.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if not user.is_entreprise or not hasattr(user, 'producer_profile'):
            context['error'] = "Accès refusé."
            return context

        context['products'] = Product.objects.filter(
            producer=user.producer_profile
        ).select_related('category').order_by('-created_at')

        return context


from django.urls import reverse_lazy
from django.contrib import messages 
from django.shortcuts import redirect
from .forms import ProductForm
from django.views.generic import CreateView, UpdateView, DeleteView

class ProductAccessMixin(LoginRequiredMixin):
    """Mixin commun pour vérifier que l'utilisateur est un producteur"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not hasattr(request.user, 'producer_profile'):
            messages.error(request, "Accès refusé : vous n'êtes pas un producteur.")
            return redirect('dashboard:index')

        return super().dispatch(request, *args, **kwargs)


# Ajout d'un produit
class AddProductView(ProductAccessMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_form.html'  # vous pouvez réutiliser ou créer un template simple
    success_url = reverse_lazy('dashboard:products')

    def form_valid(self, form):
        form.instance.producer = self.request.user.producer_profile
        messages.success(self.request, "Produit ajouté avec succès !")
        return super().form_valid(form)


# Modification d'un produit
class EditProductView(ProductAccessMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_form.html'
    success_url = reverse_lazy('dashboard:products')

    def get_queryset(self):
        """Seuls les produits du producteur connecté sont accessibles"""
        return Product.objects.filter(producer=self.request.user.producer_profile)

    def form_valid(self, form):
        messages.success(self.request, "Produit modifié avec succès !")
        return super().form_valid(form)


# Suppression d'un produit
class DeleteProductView(ProductAccessMixin, DeleteView):
    model = Product
    success_url = reverse_lazy('dashboard:products')
    template_name = 'dashboard/product_confirm_delete.html'  # optionnel, template de confirmation

    def get_queryset(self):
        return Product.objects.filter(producer=self.request.user.producer_profile)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Produit supprimé avec succès.")
        return super().delete(request, *args, **kwargs)


class OrderManagementView(LoginRequiredMixin, TemplateView):
    """Gestion des commandes reçues"""
    template_name = 'dashboard/orders.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if not user.is_entreprise or not hasattr(user, 'producer_profile'):
            context['error'] = "Accès refusé."
            return context

        orders = Order.objects.filter(
            items__product__producer=user.producer_profile
        ).distinct().select_related('client').prefetch_related('items__product').order_by('-created_at')

        context['orders'] = orders
        return context

from django.utils import timezone

class StatisticsView(LoginRequiredMixin, TemplateView):
    """Statistiques détaillées avec graphiques"""
    template_name = 'dashboard/statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        producer = user.producer_profile

        current_year = timezone.now().year

        # Commandes livrées du producteur cette année
        orders = Order.objects.filter(
            items__product__producer=producer,
            status='DELIVERED',
            created_at__year=current_year
        ).distinct()

        # Total revenus et commandes
        total_revenue = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        total_orders = orders.count()

        # Revenus par mois pour le graphique
        monthly_revenue = orders.values('created_at__month').annotate(revenue=Sum('total_amount')).order_by('created_at__month')
        monthly_orders = orders.values('created_at__month').annotate(count=Count('id')).order_by('created_at__month')

        months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
        revenue_data = [0] * 12
        orders_data = [0] * 12

        for item in monthly_revenue:
            revenue_data[item['created_at__month'] - 1] = float(item['revenue'] or 0)
        for item in monthly_orders:
            orders_data[item['created_at__month'] - 1] = item['count']

        # Meilleur mois
        best_month_idx = revenue_data.index(max(revenue_data)) if any(revenue_data) else 0
        best_month = {
            'name': months[best_month_idx],
            'revenue': revenue_data[best_month_idx]
        }

        # Progression vs mois précédent
        current_month_idx = timezone.now().month - 1
        if current_month_idx > 0 and revenue_data[current_month_idx - 1] > 0:
            monthly_growth = ((revenue_data[current_month_idx] - revenue_data[current_month_idx - 1]) / revenue_data[current_month_idx - 1]) * 100
        else:
            monthly_growth = 0

        # Produit star (le plus vendu en quantité)
        top_product_data = OrderItem.objects.filter(
            order__in=orders,
            product__producer=producer
        ).values('product__name').annotate(quantity=Sum('quantity')).order_by('-quantity').first()

        top_product = {
            'name': top_product_data['product__name'] if top_product_data else 'Aucun',
            'quantity': top_product_data['quantity'] if top_product_data else 0
        }

        context.update({
            'chart_data': {
                'labels': [f"'{m}'" for m in months],  # pour JS
                'revenue': revenue_data,
                'orders': orders_data,
            },
            'current_year': current_year,
            'best_month': best_month,
            'monthly_growth': monthly_growth,
            'top_product': top_product,
            'total_revenue': total_revenue,
            'total_orders': total_orders,
        })

        return context