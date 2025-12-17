from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.products.models import Product, Category
from apps.utilisateur.models import ProducerProfile
from apps.orders.models import Cart
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from apps.orders.models import CartItem, Order, OrderItem
from django.db import models
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from .forms import CheckoutForm
from django.http import Http404
from django.utils.http import urlencode
from django.db.models import Q

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
    """Vue HTMX pour afficher les produits populaires (sans pagination)"""
    
    products = Product.objects.filter(
        is_active=True,
        stock__gt=0
    ).order_by('-view_count')[:12] 
    cxt = {
            'products': products, 
        }
    
    return render(request, 'pages/marketplace/partials/popular_products.html', cxt)

class ProductListView(ListView):
    """Liste des produits avec recherche, filtre catégorie et tri"""
    model = Product
    template_name = 'pages/marketplace/product_list.html'
    context_object_name = 'products'
    paginate_by = 20  # Vous pouvez ajuster (12, 24, etc.)
    ordering = ['-created_at']  # Par défaut : plus récents en premier

    def get_queryset(self):
        queryset = Product.objects.filter(
            is_active=True,
            stock__gt=0
        ).select_related('producer__user', 'category').prefetch_related('producer')

        # === RECHERCHE ===
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(producer__user__username__icontains=search_query)
            )

        # === FILTRE CATÉGORIE ===
        category_id = self.request.GET.get('category')
        if category_id and category_id.isdigit():
            queryset = queryset.filter(category_id=category_id)

        # === TRI ===
        sort = self.request.GET.get('sort')
        valid_sorts = {
            'name': 'name',
            '-name': '-name',
            'price': 'price',
            '-price': '-price',
            'newest': '-created_at',
            'popularity': '-view_count',  # Si vous avez un compteur de vues
        }
        if sort in valid_sorts:
            queryset = queryset.order_by(valid_sorts[sort])
        else:
            queryset = queryset.order_by('-created_at')  # Défaut sécurisé

        return queryset.distinct()  # Évite doublons en cas de recherche complexe

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Catégories pour le filtre
        context['categories'] = Category.objects.filter(is_active=True)

        # Paramètres actuels pour conserver dans les liens de pagination/filtres
        context['current_query'] = self.request.GET.copy()

        # Pour garder les filtres actifs dans les liens de pagination
        if 'page' in context['current_query']:
            del context['current_query']['page']

        # Valeurs actuelles pour affichage (facultatif dans template)
        context['current_search'] = self.request.GET.get('search', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_sort'] = self.request.GET.get('sort', 'newest')

        # Nombre total de produits (pour affichage "X produits trouvés")
        context['total_products'] = self.get_queryset().count()

        return context

# class ProductListView(ListView):
#     """Liste des produits avec filtres"""
#     model = Product
#     template_name = 'pages/marketplace/product_list.html'
#     context_object_name = 'products'
#     paginate_by = 20
    
#     def get_queryset(self):
#         queryset = Product.objects.filter(
#             is_active=True, 
#             stock__gt=0
#         ).select_related('producer', 'category')
        
#         # Filtres
#         category = self.request.GET.get('category')
#         if category:
#             queryset = queryset.filter(category_id=category)
        
#         search = self.request.GET.get('search')
#         if search:
#             queryset = queryset.filter(
#                 name__icontains=search
#             )
        
#         sort = self.request.GET.get('sort', '-created_at')
#         return queryset.order_by(sort)
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['categories'] = Category.objects.filter(is_active=True)
#         return context


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

@require_http_methods(["POST"])
@login_required  # Plus propre que vérifier manuellement
def add_to_cart(request, product_id):
    product = get_object_or_404(
        Product, 
        id=product_id, 
        is_active=True, 
        stock__gt=0
    )

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, f"{product.name} ajouté au panier !")

    # Calcul du nombre total d'articles
    total_items = cart.items.aggregate(total=models.Sum('quantity'))['total'] or 0

    # Snippet pour le compteur dans la navbar
    count_snippet = f'''
        <span id="cart-count" class="badge badge-success rounded-pill px-3 py-2">
            <i class="fas fa-shopping-cart me-2"></i> {total_items}
        </span>
    '''

    # Si la requête vient de la page panier, on renvoie aussi le partial mis à jour
    if request.htmx and request.headers.get('HX-Current-URL', '').endswith('/cart/'):
        # On est sur la page panier → on renvoie le partial complet des items
        from django.shortcuts import render
        return render(request, 'marketplace/partials/cart_items.html', {'cart': cart})

    # Sinon, on renvoie juste le compteur mis à jour
    response = HttpResponse(count_snippet)
    return response


@require_http_methods(["POST"])
@login_required
def update_cart_quantity(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    # Récupère le changement de quantité depuis hx-vals
    try:
        quantity_change = int(request.POST.get('quantity_change', 0))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Changement de quantité invalide")

    new_quantity = cart_item.quantity + quantity_change

    if new_quantity <= 0:
        # Si on descend à 0 ou moins → on supprime l'article
        cart_item.delete()
        messages.info(request, f"{cart_item.product.name} supprimé du panier.")
    else:
        # Vérifie le stock disponible
        if new_quantity > cart_item.product.stock:
            messages.error(request, f"Stock insuffisant : seulement {cart_item.product.stock} disponible(s).")
            new_quantity = cart_item.product.stock

        cart_item.quantity = new_quantity
        cart_item.save()
        messages.success(request, f"Quantité mise à jour : {new_quantity} × {cart_item.product.name}")

    # Récupère le panier mis à jour pour le partial
    cart = Cart.objects.get(user=request.user)

    # Retourne le partial mis à jour
    return render(request, 'pages/marketplace/partials/cart_items.html', {'cart': cart})


@require_http_methods(["DELETE"])
@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    product_name = cart_item.product.name
    cart_item.delete()
    
    messages.success(request, f"{product_name} supprimé du panier.")

    # Récupère le panier (peut être vide maintenant)
    cart, _ = Cart.objects.get_or_create(user=request.user)

    # Retourne le partial mis à jour (liste vide si plus rien)
    return render(request, 'pages/marketplace/partials/cart_items.html', {'cart': cart})



import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class CheckoutView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/marketplace/checkout.html'

    def dispatch(self, request, *args, **kwargs):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        if not cart.items.exists():
            messages.warning(request, "Votre panier est vide.")
            return redirect('marketplace:cart')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cart = Cart.objects.get(user=self.request.user)
        context['cart'] = cart
        context['total_amount'] = cart.get_total_amount()

        # Formulaire d'adresse (avec données déjà saisies si POST invalide)
        if 'form' in kwargs:
            context['form'] = kwargs['form']
        else:
            initial = self.request.session.get('checkout_data', {})
            context['form'] = CheckoutForm(initial=initial)

        # Création du PaymentIntent à chaque GET (recommandé par Stripe)
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(cart.get_total_amount() * 100),
                currency='eur',
                automatic_payment_methods={'enabled': True},
                metadata={
                    'user_id': str(self.request.user.id),
                    'cart_id': str(cart.id),
                },
            )
            context['client_secret'] = intent.client_secret
            context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
        except Exception as e:
            messages.error(self.request, "Impossible de préparer le paiement. Veuillez réessayer.")
            context['payment_error'] = True  # Optionnel : pour afficher un message dans le template

        return context

    def post(self, request, *args, **kwargs):
        """Seulement pour valider le formulaire d'adresse"""
        cart = Cart.objects.get(user=request.user)

        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Sauvegarde temporaire des données d'adresse dans la session
            request.session['checkout_data'] = form.cleaned_data
            messages.success(request, "Adresse enregistrée. Vous pouvez maintenant payer.")
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire d'adresse.")

        # On recharge la page avec le formulaire mis à jour
        kwargs['form'] = form
        return self.render_to_response(self.get_context_data(**kwargs))

# stripe.api_key = settings.STRIPE_SECRET_KEY
@login_required
def payment_success(request):
    # Récupère le payment_intent depuis Stripe (passé en query param par return_url)
    payment_intent_id = request.GET.get('payment_intent')
    if not payment_intent_id:
        messages.error(request, "Aucun paiement détecté.")
        return redirect('marketplace:cart')

    try:
        # Récupère et vérifie le PaymentIntent auprès de Stripe
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if intent.status != 'succeeded':
            messages.error(request, "Le paiement n'a pas abouti.")
            return redirect('marketplace:cart')

        # Sécurité : vérifie que ce paiement appartient bien à l'utilisateur
        if intent.metadata.get('user_id') != str(request.user.id):
            raise Http404("Commande non autorisée")

        cart = get_object_or_404(Cart, user=request.user)

        # Récupère les données d'adresse sauvegardées dans la session (depuis checkout)
        order_data = request.session.get('checkout_data')
        if not order_data:
            messages.error(request, "Informations de livraison manquantes.")
            return redirect('marketplace:cart')

        # Génération manuelle du numéro de commande (car on a besoin du PK après création)
        # On crée d'abord l'objet pour obtenir le PK
        order = Order.objects.create(
            client=request.user,
            status=Order.Status.CONFIRMED,
            shipping_address=f"{order_data['address_line_1']}\n"
                            f"{order_data.get('address_line_2', '')}\n"
                            f"{order_data['postal_code']} {order_data['city']}",
            notes=order_data.get('notes', ''),
            total_amount=cart.get_total_amount(),
            payment_intent_id=payment_intent_id,
            payment_status='paid',
        )

        # Maintenant qu'on a le PK, on génère le numéro de commande
        order.order_number = order.generate_order_number()
        order.save(update_fields=['order_number'])

        # Création des OrderItem
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.price,
                subtotal=cart_item.get_subtotal()
            )

            # Optionnel : Décrémenter le stock du produit
            product = cart_item.product
            product.stock -= cart_item.quantity
            product.save()

        # Vidage du panier
        cart.items.all().delete()

        # Nettoyage de la session
        if 'checkout_data' in request.session:
            del request.session['checkout_data']
        if 'payment_intent_id' in request.session:
            del request.session['payment_intent_id']
        if 'client_secret' in request.session:
            del request.session['client_secret']

        messages.success(request, f"Votre commande {order.order_number} a été confirmée avec succès !")

        context = {
            'order': order,
        }
        return render(request, 'pages/marketplace/payment_success.html', context)

    except stripe.error.StripeError as e:
        messages.error(request, "Erreur lors de la vérification du paiement.")
        return redirect('marketplace:cart')
    except Exception as e:
        messages.error(request, "Une erreur inattendue est survenue.")
        return redirect('marketplace:cart')
