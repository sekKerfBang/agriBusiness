from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='index'),
    path('products/', views.ProductManagementView.as_view(), name='products'),
    path('orders/', views.OrderManagementView.as_view(), name='orders'),
    path('statistics/', views.StatisticsView.as_view(), name='statistics'),
]