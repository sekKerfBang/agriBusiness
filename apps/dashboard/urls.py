from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='index'),
    path('products/', views.ProductManagementView.as_view(), name='products'),
    path('products/add/', views.AddProductView.as_view(), name='add_product'),
    path('products/<int:pk>/edit/', views.EditProductView.as_view(), name='edit_product'),
    path('products/<int:pk>/delete/', views.DeleteProductView.as_view(), name='delete_product'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('orders/', views.OrderManagementView.as_view(), name='orders'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'), 
    path('statistics/', views.StatisticsView.as_view(), name='statistics'),
]