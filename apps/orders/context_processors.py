from django.db.models import Sum
from apps.orders.models import Cart


def cart_context(request):
    cart_count = 0
    if request.user.is_authenticated:
        try:
            # Grâce au OneToOneField + related_name='cart'
            cart = request.user.cart
            total = cart.items.aggregate(total=Sum('quantity'))['total']
            cart_count = total or 0
        except Cart.DoesNotExist:
            cart_count = 0
        except AttributeError:
            cart_count = 0

    return {'cart_count': cart_count}

# def cart_context(request):
#     if request.user.is_authenticated:
#         try:
#             cart = request.user.cart
#             count = cart.items.aggregate(total=Sum('quantity'))['total'] or 0
#         except Cart.DoesNotExist:
#             count = 0
#         except AttributeError:
#             count = 0
#     else:
#         count = 0

#     return {
#         'cart_count': count,
#         # Bonus : tu peux même passer le cart entier si tu veux
#         # 'cart': cart if request.user.is_authenticated else None
#     }
# # apps/orders/context_processors.py
