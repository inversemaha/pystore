from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('products/', TemplateView.as_view(template_name='products.html'), name='products'),
    path('product/<slug:slug>/', TemplateView.as_view(template_name='product_detail.html'), name='product_detail'),
    path('cart/', TemplateView.as_view(template_name='cart.html'), name='cart'),
    path('checkout/', TemplateView.as_view(template_name='checkout.html'), name='checkout'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register'),
    path('orders/', TemplateView.as_view(template_name='orders.html'), name='orders'),
]