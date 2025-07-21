from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('auth', views.AuthViewSet, basename='auth')
router.register('categories', views.CategoryViewSet)
router.register('products', views.ProductViewSet)
router.register('cart', views.CartViewSet, basename='cart')
router.register('orders', views.OrderViewSet, basename='orders')

urlpatterns = [
    path('', include(router.urls)),
]