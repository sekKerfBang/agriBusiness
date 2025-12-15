from .models import Cart  # Adap
from django.db import models

def cart_count(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        count = cart.items.aggregate(total=models.Sum('quantity'))['total'] or 0 if cart else 0
    else:
        count = 0  # Ou session si non auth
    return {'cart_count': count}