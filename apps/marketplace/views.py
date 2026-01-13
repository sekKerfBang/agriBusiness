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


## cette class est pour afficher la liste des producteurs 
class ProducerListView(ListView):
    """Liste des producteurs"""
    model = ProducerProfile
    template_name = 'pages/marketplace/producer_list.html'
    context_object_name = 'producers'
    
    def get_queryset(self):
        return ProducerProfile.objects.filter(validated=True).select_related('user')

## cette class est pour afficher les détails d'un produit
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

## cette class est pour afficher le panier
class CartView(LoginRequiredMixin, TemplateView):
    """Page du panier"""
    template_name = 'pages/marketplace/cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            try:
                context['cart'] = self.request.user.cart
            except Cart.DoesNotExist:
                # Crée le panier s'il n'existe pas
                context['cart'] = Cart.objects.create(user=self.request.user)
        else:
            context['cart'] = None  # ou redirige vers login
        return context
    
from django.urls import reverse
from django.template.loader import render_to_string


## cette def est pour ajouter un produit au panier
@login_required
@require_http_methods(["POST"])
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

    if request.htmx:
        if request.path == reverse('marketplace:cart'):
            # Sur la page panier → on renvoie le partial + messages en OOB
            context = {'cart': cart}
            main_content = render_to_string('pages/marketplace/partials/cart_items.html', context, request=request)
            messages_content = render_to_string('pages/marketplace/partials/messages.html', request=request)

            full_html = f"""
            {main_content}
            <div id="messages-container" hx-swap-oob="innerHTML">{messages_content}</div>
            """
            return HttpResponse(full_html)

        # Hors page panier → juste feedback bouton, réponse vide
        return HttpResponse("")

    return redirect('marketplace:cart')

# cette def est pour mettre à jour la quantité d'un article dans le panier
@login_required
@require_http_methods(["POST"])
def update_cart_quantity(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    try:
        quantity_change = int(request.POST.get('quantity_change', 0))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Changement de quantité invalide")

    new_quantity = cart_item.quantity + quantity_change

    if new_quantity <= 0:
        cart_item.delete()
        messages.info(request, "Article supprimé du panier.")
    else:
        if new_quantity > cart_item.product.stock:
            messages.error(request, f"Stock insuffisant : seulement {cart_item.product.stock} disponible(s).")
            new_quantity = cart_item.product.stock

        cart_item.quantity = new_quantity
        cart_item.save()
        messages.success(request, f"Quantité mise à jour : {new_quantity} × {cart_item.product.name}")

    cart = request.user.cart

    # Rendu du contenu principal
    main_content = render_to_string('pages/marketplace/partials/cart_items.html', {'cart': cart}, request=request)
    messages_content = render_to_string('pages/marketplace/partials/messages.html', request=request)

    # Assemblage avec OOB pour les messages
    full_html = f"""
    {main_content}
    <div id="messages-container" hx-swap-oob="innerHTML">
        {messages_content}
    </div>
    """

    return HttpResponse(full_html)

## cette def est pour supprimer un article du panier
@login_required
@require_http_methods(["DELETE"])
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    product_name = cart_item.product.name
    cart_item.delete()

    messages.success(request, f"{product_name} supprimé du panier.")

    cart, _ = Cart.objects.get_or_create(user=request.user)

    # Rendu du contenu principal
    main_content = render_to_string('pages/marketplace/partials/cart_items.html', {'cart': cart}, request=request)
    messages_content = render_to_string('pages/marketplace/partials/messages.html', request=request)

    # Assemblage avec OOB
    full_html = f"""
    {main_content}
    <div id="messages-container" hx-swap-oob="innerHTML">
        {messages_content}
    </div>
    """

    return HttpResponse(full_html)


## cet def est pour afficher les messages du panier
def cart_messages(request):
    return render(request, 'pages/marketplace/partials/messages.html')




import stripe
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.contrib import messages
from .services import PaymentService

import environ
env = environ.Env()



## cette clef est pour la configuration de stripe
stripe.api_key = env('STRIPE_SECRET_KEY')


class CheckoutView(LoginRequiredMixin, FormView):
    template_name = 'pages/marketplace/checkout.html' 
    form_class = CheckoutForm
    success_url = reverse_lazy('marketplace:payment_success')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.request.user.cart
        total = cart.get_total_amount()
        context['cart'] = cart
        context['stripe_public_key'] = env('STRIPE_PUBLISHABLE_KEY')
        context['total_amount'] = total

        # Créer intent ici (sur GET)
        try:
            intent = PaymentService.create_payment_intent(  # Assume ton service
                amount=total,
                currency='gnf',
                metadata={'user_id': self.request.user.id, 'cart_id': cart.id}
            )
            self.request.session['payment_intent_id'] = intent.id
            context['client_secret'] = intent.client_secret  # Ajout clé !
        except Exception as e:
            messages.error(self.request, "Erreur création paiement.")
            context['client_secret'] = None

        return context

    def form_valid(self, form):
        # Plus besoin de créer intent ici, car déjà fait. form_valid pas appelé anyway (JS bloque POST).
        # Si tu gardes HTMX pour autre chose, adapte.
        return super().form_valid(form)




from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json

## cette def est pour le webhook de stripe lui permettant de notifier l'application des événements de paiement
@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        # Mettre à jour l'ordre en base : status = 'PAID'
        order = Order.objects.get(payment_intent_id=intent.id)
        order.status = 'PAID'
        order.save()
        # Envoyer email confirmation

    return HttpResponse(status=200)

@login_required
@require_POST
def store_checkout_data(request):
    try:
        data = json.loads(request.body)
        # Valide data (optionnel : use CheckoutForm pour clean)
        form = CheckoutForm(data)
        if not form.is_valid():
            return JsonResponse({'error': form.errors}, status=400)

        # Stocker en session
        request.session['checkout_data'] = form.cleaned_data

        # Optionnel : update intent metadata avec notes ou adresse JSON
        intent_id = request.session.get('payment_intent_id')
        if intent_id:
            stripe.PaymentIntent.modify(
                intent_id,
                metadata={'notes': form.cleaned_data.get('notes', '')}  # Ou JSON adresse si besoin
            )

        return JsonResponse({'status': 'ok'})
    except Exception as e:
        logger.error(f"Erreur store data: {e}")
        return JsonResponse({'error': 'Erreur serveur'}, status=500)


from django.core.mail import send_mail
import logging
logger = logging.getLogger(__name__)



@login_required
def payment_success(request):
    payment_intent_id = request.GET.get('payment_intent')
    if not payment_intent_id:
        messages.error(request, "Aucun paiement détecté.")
        return redirect('marketplace:cart')

    stripe.api_key = env('STRIPE_SECRET_KEY')

    try:
        # Récupère et vérifie le PaymentIntent auprès de Stripe
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if intent.status != 'succeeded':
            messages.error(request, "Le paiement n'a pas abouti.")
            return redirect('marketplace:cart')

        # Sécurité : vérifie metadata (user_id et cart_id)
        if intent.metadata.get('user_id') != str(request.user.id):
            messages.error(request, "Paiement non autorisé.")
            return redirect('marketplace:cart')

        cart = get_object_or_404(Cart, user=request.user, id=intent.metadata.get('cart_id', 0))

        # Récupère les données de livraison de la session
        order_data = request.session.get('checkout_data')
        if not order_data:
            messages.error(request, "Informations de livraison manquantes.")
            return redirect('marketplace:cart')

        # Création de l'ordre
        order = Order(
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
        order.save()  # Sauvegarde d'abord pour obtenir le PK

        # Génération du numéro de commande (basé sur PK)
        order.order_number = order.generate_order_number()
        order.save(update_fields=['order_number'])

        # Création des OrderItem + mise à jour stock
        for cart_item in cart.items.all():
            product = cart_item.product
            if product.stock < cart_item.quantity:
                messages.warning(request, f"Stock insuffisant pour {product.name}. Commande partielle.")
                cart_item.quantity = product.stock  # Ajuste quantité max

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=cart_item.quantity,
                unit_price=product.price,
                subtotal=cart_item.get_subtotal()
            )

            # Mise à jour stock produit
            product.stock -= cart_item.quantity
            product.save()

        # Vidage du panier
        cart.items.all().delete()

        # Nettoyage session
        request.session.pop('checkout_data', None)
        request.session.pop('payment_intent_id', None)
        request.session.pop('client_secret', None)

        # Envoi email confirmation (optionnel)
        try:
            send_mail(
                subject=f"Confirmation de commande #{order.order_number}",
                message=f"Merci pour votre commande de {order.total_amount} GNF !\nDétails : {order.shipping_address}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
            )
            logger.info(f"Email confirmation envoyé pour commande {order.order_number}")
        except Exception as e:
            logger.error(f"Erreur envoi email commande {order.order_number}: {e}")
            messages.warning(request, "Commande confirmée, mais email non envoyé. Vérifiez votre spam.")

        messages.success(request, f"Votre commande {order.order_number} a été confirmée avec succès !")
        context = {'order': order}
        return render(request, 'pages/marketplace/payment_success.html', context)

    except stripe.error.StripeError as e:
        logger.error(f"Erreur Stripe paiement success: {e}")
        messages.error(request, "Erreur lors de la vérification du paiement.")
        return redirect('marketplace:cart')
    except Exception as e:
        logger.error(f"Erreur générale paiement success: {e}")
        messages.error(request, "Une erreur inattendue est survenue.")
        return redirect('marketplace:cart')
    
from django.db import transaction

@login_required
@transaction.atomic  # Tout ou rien : synchronisation parfaite
def payment_success(request):
    payment_intent_id = request.GET.get('payment_intent')
    if not payment_intent_id:
        messages.error(request, "Aucun paiement détecté.")
        return redirect('marketplace:cart')

    stripe.api_key = env('STRIPE_SECRET_KEY')

    try:
        # Vérifie PaymentIntent
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if intent.status != 'succeeded':
            messages.error(request, "Le paiement n'a pas abouti.")
            return redirect('marketplace:cart')

        # Sécurité metadata
        if intent.metadata.get('user_id') != str(request.user.id):
            messages.error(request, "Paiement non autorisé.")
            return redirect('marketplace:cart')

        cart = get_object_or_404(Cart, user=request.user)

        # Données livraison de session
        order_data = request.session.get('checkout_data')
        if not order_data:
            messages.error(request, "Informations de livraison manquantes.")
            return redirect('marketplace:cart')

        # Création order
        order = Order(
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
        order.save()  # Sauvegarde pour PK

        # Génération numéro (avec PK)
        order.order_number = order.generate_order_number()
        order.save(update_fields=['order_number'])

        # Ajout OrderItem + maj stock (sync)
        for cart_item in cart.items.all():
            product = cart_item.product
            if product.stock < cart_item.quantity:
                messages.warning(request, f"Stock insuffisant pour {product.name}. Quantité ajustée.")
                cart_item.quantity = product.stock

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=cart_item.quantity,
                unit_price=product.price,
                subtotal=cart_item.get_subtotal()
            )

            product.stock -= cart_item.quantity
            product.save()

        # Vidage panier
        cart.items.all().delete()

        # Nettoyage session
        request.session.pop('checkout_data', None)

        # Envoi email (optionnel)
        send_mail(
            'Confirmation de commande',
            f'Votre commande {order.order_number} a été confirmée ! Montant: {order.total_amount} GNF.',
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=True
        )

        messages.success(request, f"Commande {order.order_number} confirmée !")
        return render(request, 'pages/marketplace/payment_success.html', {'order': order})

    except stripe.error.StripeError as e:
        logger.error(f"Erreur Stripe: {e}")
        messages.error(request, "Erreur vérification paiement.")
        return redirect('marketplace:cart')
    except Exception as e:
        logger.error(f"Erreur générale: {e}")
        messages.error(request, "Erreur inattendue.")
        return redirect('marketplace:cart')    