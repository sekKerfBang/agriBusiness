from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.MarketplaceHomeView.as_view(), name='home'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('producers/', views.ProducerListView.as_view(), name='producer_list'),
    path('producers/<int:pk>/', views.ProducerDetailView.as_view(), name='producer_detail'),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/messages/', views.cart_messages, name='cart_messages'),
    # path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    # 🔥 HTMX endpoint
    path(
        'popular-products/',views.popular_products_htmx, name='popular_products'),

    # Payment endpoint
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('payment/success/', views.payment_success, name='payment_success'),
    # path('payment-success/', views.PaymentSuccessView.as_view(), name='payment_success'),    
]