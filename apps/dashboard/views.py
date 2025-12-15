from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from apps.products.models import Product
from apps.orders.models import Order


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


class StatisticsView(LoginRequiredMixin, TemplateView):
    """Statistiques détaillées avec graphiques"""
    template_name = 'dashboard/statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if not user.is_entreprise or not hasattr(user, 'producer_profile'):
            context['error'] = "Accès refusé."
            return context

        producer = user.producer_profile

        # Ventes par mois (pour Chart.js)
        monthly_data = Order.objects.filter(
            items__product__producer=producer,
            status='DELIVERED'
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            revenue=Sum('total_amount'),
            orders_count=Count('id')
        ).order_by('month')

        # Format pour Chart.js
        labels = [item['month'].strftime('%b %Y') for item in monthly_data]
        revenue_data = [float(item['revenue'] or 0) for item in monthly_data]
        orders_data = [item['orders_count'] for item in monthly_data]

        context['chart_data'] = {
            'labels': labels,
            'revenue': revenue_data,
            'orders': orders_data,
        }

        return context