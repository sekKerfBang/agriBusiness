from django.db.models import Sum
from apps.orders.models import Cart

def cart_context(request):
    if request.user.is_authenticated:
        try:
            cart = request.user.cart
            count = cart.items.aggregate(total=Sum('quantity'))['total'] or 0
        except Cart.DoesNotExist:
            count = 0
        except AttributeError:
            count = 0
    else:
        count = 0

    return {
        'cart_count': count,
        # Bonus : tu peux même passer le cart entier si tu veux
        # 'cart': cart if request.user.is_authenticated else None
    }