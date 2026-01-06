from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, DetailView
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from apps.products.models import Product
from apps.orders.models import Order, OrderItem
from datetime import datetime, timedelta
from django.shortcuts import redirect
from django.utils import timezone
from apps.utilisateur.models import ProducerProfile


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # 1. Vérification que l'utilisateur est un producteur
        if not user.is_entreprise:
            context['error'] = "Accès réservé aux producteurs. <a href='/marketplace/'>Retour au marché</a>."
            context.update(self.get_empty_context())
            return context

        # 2. Vérification du ProducerProfile
        try:
            producer_profile = user.producer_profile

        except AttributeError:
            # Si le related_name est mal configuré
            context['error'] = "Erreur de configuration du profil producteur. Contactez l'administrateur."
            context.update(self.get_empty_context())
            return context
        except ProducerProfile.DoesNotExist:
            # Profil producteur manquant → on redirige vers édition pour le créer automatiquement
            return redirect('utilisateur:profile_edit')

        # 3. Tout est bon → on récupère les données réelles
        products_qs = Product.objects.filter(producer=producer_profile)

        # Commandes liées aux produits du producteur (via OrderItem)
        orders_qs = Order.objects.filter(items__product__producer=producer_profile).distinct()

        # Période pour la tendance CA (30 derniers jours)
        now = datetime.now()
        last_30_days = now - timedelta(days=30)
        previous_30_days_start = last_30_days - timedelta(days=30)

        recent_orders_period = orders_qs.filter(created_at__gte=last_30_days)
        previous_orders_period = orders_qs.filter(
            created_at__gte=previous_30_days_start,
            created_at__lt=last_30_days
        )

        recent_revenue = recent_orders_period.aggregate(total=Sum('total_amount'))['total'] or 0
        previous_revenue = previous_orders_period.aggregate(total=Sum('total_amount'))['total'] or 0

        # Calcul de la tendance
        if previous_revenue > 0:
            revenue_trend = ((recent_revenue - previous_revenue) / previous_revenue) * 100
        elif recent_revenue > 0:
            revenue_trend = 100.0  # Première vente
        else:
            revenue_trend = 0.0

        # Stats complètes
        context['stats'] = {
            'total_products': products_qs.count(),
            'active_products': products_qs.filter(is_active=True).count(),
            'total_orders': orders_qs.count(),
            'pending_orders': orders_qs.filter(status__in=['PENDING', 'CONFIRMED', 'PREPARING']).count(),
            'revenue': orders_qs.filter(status='DELIVERED').aggregate(total=Sum('total_amount'))['total'] or 0,
            'revenue_trend': round(revenue_trend, 1),
            'low_stock': products_qs.filter(stock__lt=10, stock__gt=0).count(),
            'out_of_stock': products_qs.filter(stock=0).count(),
            'monthly_revenue': recent_revenue,
        }

        context['recent_orders'] = orders_qs.order_by('-created_at')[:8]
        context['stock_alerts'] = products_qs.filter(stock__lt=10).order_by('stock')[:8]
        context['has_data'] = products_qs.exists() or orders_qs.exists()

        return context

    def get_empty_context(self):
        """Retourne les données vides pour éviter les erreurs de template"""
        return {
            'stats': {
                'total_products': 0,
                'active_products': 0,
                'total_orders': 0,
                'pending_orders': 0,
                'revenue': 0,
                'revenue_trend': 0,
                'low_stock': 0,
                'out_of_stock': 0,
                'monthly_revenue': 0,
            },
            'recent_orders': [],
            'stock_alerts': [],
            'has_data': False,
        }

# class DashboardView(LoginRequiredMixin, TemplateView):
#     template_name = 'dashboard/index.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         user = self.request.user

#         # Vérification accès producteur
#         if not user.is_entreprise:
#             context['error'] = "Accès réservé aux producteurs. <a href='/marketplace/'>Retour au marché</a>."
#             context['stats'] = self.get_empty_stats()
#             context['recent_orders'] = []
#             context['stock_alerts'] = []
#             return context

#         try:
#             producer_profile = user.producerprofile  # grâce au related_name
#         except AttributeError:
#             context['error'] = "Votre profil producteur est incomplet. <a href='/profile/edit/'>Complétez-le ici</a>."
#             context['stats'] = self.get_empty_stats()
#             context['recent_orders'] = []
#             context['stock_alerts'] = []
#             return context

#         # Récupération des produits du producteur
#         products_qs = Product.objects.filter(producer=producer_profile)

#         # Commandes liées aux produits du producteur
#         orders_qs = Order.objects.filter(items__product__producer=producer_profile).distinct()

#         # Période pour les tendances (30 derniers jours)
#         last_30_days = datetime.now() - timedelta(days=30)
#         recent_orders = orders_qs.filter(created_at__gte=last_30_days)
#         previous_orders = orders_qs.filter(created_at__lt=last_30_days, created_at__gte=last_30_days - timedelta(days=30))

#         recent_revenue = recent_orders.aggregate(total=Sum('total_amount'))['total'] or 0
#         previous_revenue = previous_orders.aggregate(total=Sum('total_amount'))['total'] or 0

#         # Calcul tendance CA
#         if previous_revenue > 0:
#             revenue_trend = ((recent_revenue - previous_revenue) / previous_revenue) * 100
#         else:
#             revenue_trend = 100 if recent_revenue > 0 else 0

#         context['stats'] = {
#             'total_products': products_qs.count(),
#             'active_products': products_qs.filter(is_active=True).count(),
#             'total_orders': orders_qs.count(),
#             'pending_orders': orders_qs.filter(status__in=['PENDING', 'CONFIRMED', 'PREPARING']).count(),
#             'revenue': orders_qs.filter(status='DELIVERED').aggregate(total=Sum('total_amount'))['total'] or 0,
#             'revenue_trend': round(revenue_trend, 1),
#             'low_stock': products_qs.filter(stock__lt=10, stock__gt=0).count(),
#             'out_of_stock': products_qs.filter(stock=0).count(),
#             'monthly_revenue': recent_revenue,
#         }

#         context['recent_orders'] = orders_qs.order_by('-created_at')[:8]
#         context['stock_alerts'] = products_qs.filter(stock__lt=10).order_by('stock')[:8]
#         context['has_data'] = products_qs.exists() or orders_qs.exists()

#         return context

#     def get_empty_stats(self):
#         return {
#             'total_products': 0,
#             'active_products': 0,
#             'total_orders': 0,
#             'pending_orders': 0,
#             'revenue': 0,
#             'revenue_trend': 0,
#             'low_stock': 0,
#             'out_of_stock': 0,
#             'monthly_revenue': 0,
#         }

# class DashboardView(LoginRequiredMixin, TemplateView):
#     """Dashboard principal du producteur"""
#     template_name = 'dashboard/index.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         user = self.request.user

#         if not user.is_entreprise or not hasattr(user, 'producer_profile'):
#             context['error'] = "Vous n'avez pas accès au dashboard producteur. <a href='/marketplace/'>Retour au marché</a>."
#             # Defaults vides pour éviter erreurs
#             context['stats'] = {'total_products': 0, 'active_products': 0, 'total_orders': 0, 'revenue': 0, 'pending_orders': 0, 'low_stock': 0}
#             context['recent_orders'] = []
#             context['stock_alerts'] = []
#             return context

#         producer = user.producer_profile
#         products_qs = Product.objects.filter(producer=producer)
#         orders_qs = Order.objects.filter(items__product__in=products_qs).distinct()

#         # Stats (comme ton code)
#         context['stats'] = {
#             'total_products': products_qs.count(),
#             'active_products': products_qs.filter(is_active=True).count(),
#             'total_orders': orders_qs.count(),
#             'pending_orders': orders_qs.filter(status='PENDING').count(),
#             'revenue': orders_qs.filter(status='DELIVERED').aggregate(total=Sum('total_amount'))['total'] or 0,
#             'low_stock': products_qs.filter(stock__lt=10).count(),
#         }

#         context['recent_orders'] = orders_qs.order_by('-created_at')[:6]
#         context['stock_alerts'] = products_qs.filter(stock__lt=10).order_by('stock')[:6]

#         return context

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
# cette classe mixin peut être utilisée pour les vues de gestion des produits
class ProductDetailView(DetailView):
    model = Product
    template_name = 'dashboard/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Vous pouvez ajouter des données supplémentaires ici si nécessaire
        return context


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
from django.views import View
from django.shortcuts import get_object_or_404, render

class DeleteProductView(ProductAccessMixin, View):
    template_name = 'dashboard/product_confirm_delete.html'  # le template de confirmation

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk, producer=request.user.producer_profile)
        return render(request, self.template_name, {'object': product})

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk, producer=request.user.producer_profile)
        
        if product.order_items.exists():
            product.is_active = False
            product.save()
            messages.warning(
                request,
                f'Le produit "{product.name}" a été désactivé (il a été commandé par des clients). '
                f'Il n\'est plus visible à la vente, mais conservé pour l\'historique des commandes.'
            )
        else:
            product.delete()
            messages.success(request, f'Le produit "{product.name}" a été supprimé définitivement.')
        
        return redirect('dashboard:products')
    
# class DeleteProductView(ProductAccessMixin, DeleteView):
#     model = Product
#     success_url = reverse_lazy('dashboard:products')
#     template_name = 'dashboard/product_confirm_delete.html'  # optionnel, template de confirmation

#     def get_queryset(self):
#         return Product.objects.filter(producer=self.request.user.producer_profile)

#     def delete(self, request, *args, **kwargs):
#         messages.success(request, "Produit supprimé avec succès.")
#         return super().delete(request, *args, **kwargs)

## COMMANDES CLASS
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
    

class OrderDetailView(ProductAccessMixin, DetailView):
    model = Order
    template_name = 'dashboard/orders_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        """Seules les commandes contenant un produit du producteur connecté"""
        producer = self.request.user.producer_profile
        return Order.objects.filter(items__product__producer=producer).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_items'] = self.object.items.select_related('product').all()
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