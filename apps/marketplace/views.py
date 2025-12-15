from django.shortcuts import render
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.products.models import Product, Category
from apps.utilisateur.models import ProducerProfile
from apps.orders.models import Cart
from django.core.paginator import Paginator

class MarketplaceHomeView(TemplateView):
    """Page d'accueil du marché"""
    template_name = 'pages/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_products'] = Product.objects.filter(
            is_active=True, 
            stock__gt=0
        )[:6]
        context['categories'] = Category.objects.filter(is_active=True)
        context['producers'] = ProducerProfile.objects.filter(
            validated=True
        )[:6]
        return context
    
def popular_products_htmx(request):
    products = Product.objects.filter(
        is_active=True,
        stock__gt=0
    ).order_by('-view_count')[:20] 
    
    # Pagination optionnelle (pour 6 par page)
    paginator = Paginator(products, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(
        request,
        'pages/marketplace/partials/popular_products.html',
        {
            'products': page_obj.object_list, 
            'page_obj': page_obj, 
            'is_paginated': page_obj.has_other_pages()
            }
    )


class ProductListView(ListView):
    """Liste des produits avec filtres"""
    model = Product
    template_name = 'pages/marketplace/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.filter(
            is_active=True, 
            stock__gt=0
        ).select_related('producer', 'category')
        
        # Filtres
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                name__icontains=search
            )
        
        sort = self.request.GET.get('sort', '-created_at')
        return queryset.order_by(sort)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        return context


class ProducerListView(ListView):
    """Liste des producteurs"""
    model = ProducerProfile
    template_name = 'pages/marketplace/producer_list.html'
    context_object_name = 'producers'
    
    def get_queryset(self):
        return ProducerProfile.objects.filter(validated=True).select_related('user')


class ProducerDetailView(DetailView):
    """Détail d'un producteur avec ses produits"""
    model = ProducerProfile
    template_name = 'pages/marketplace/producer_detail.html'
    context_object_name = 'producer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = self.object.products.filter(
            is_active=True,
            stock__gt=0
        )
        return context


class CartView(LoginRequiredMixin, TemplateView):
    """Page du panier"""
    template_name = 'pages/marketplace/cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        context['cart'] = cart  # Passe au template
        return context

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from apps.orders.models import CartItem
from django.db import models

@require_http_methods(["POST"])
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return HttpResponse("Connectez-vous pour ajouter au panier", status=401)
    
    product = get_object_or_404(Product, id=product_id, is_active=True, stock__gt=0)
    
    # Logique d'ajout au panier (adapte à ton modèle)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    if not item_created:
        cart_item.quantity += 1
        cart_item.save()
    
    # Message de succès (optionnel, pour session)
    messages.success(request, f'{product.name} ajouté au panier !')
    
    # Retourne un snippet HTML pour HTMX (juste le compteur mis à jour)
    total_items = cart.items.aggregate(total=models.Sum('quantity'))['total'] or 0
    snippet = f'<span id="cart-count"><i class="fas fa-shopping-cart"></i> {total_items} articles</span>'
    
    return HttpResponse(snippet)    


class CheckoutView(LoginRequiredMixin, TemplateView):
    """Page de paiement"""
    template_name = 'pages/marketplace/checkout.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = Cart.objects.filter(user=self.request.user).first()
        context['cart'] = cart if cart else Cart.objects.create(user=self.request.user)
        context['total_amount'] = context['cart'].get_total_amount()  # Passe le total
        return context