from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import *
from .serializers import *

class AuthViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'message': 'Registration successful',
                'token': token.key,
                'user_id': user.id,
                'email': user.email
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            login(request, user)
            return Response({
                'message': 'Login successful',
                'token': token.key,
                'user_id': user.id,
                'email': user.email
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        try:
            request.user.auth_token.delete()
        except:
            pass
        logout(request)
        return Response({'message': 'Logout successful'})

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True).prefetch_related('images', 'variants', 'category')
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category_slug = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured_products = self.get_queryset().filter(is_featured=True)
        serializer = self.get_serializer(featured_products, many=True)
        return Response(serializer.data)

class CartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        variant_id = request.data.get('variant_id')
        quantity = int(request.data.get('quantity', 1))
        
        try:
            variant = ProductVariant.objects.get(id=variant_id)
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product_variant=variant,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            return Response({'message': 'Item added to cart'}, status=status.HTTP_201_CREATED)
        except ProductVariant.DoesNotExist:
            return Response({'error': 'Product variant not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['put'])
    def update_item(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity'))
        
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            if quantity <= 0:
                cart_item.delete()
                return Response({'message': 'Item removed from cart'})
            else:
                cart_item.quantity = quantity
                cart_item.save()
                return Response({'message': 'Cart updated'})
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

class OrderViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        order = get_object_or_404(Order, id=pk, user=request.user)
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def create_order(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        if not cart.items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate totals
        subtotal = sum(item.total_price for item in cart.items.all())
        shipping_cost = 50 if subtotal < 999 else 0
        tax_amount = subtotal * 0.18
        total_amount = subtotal + shipping_cost + tax_amount
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            order_number=f"ORD{Order.objects.count() + 1:06d}",
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            total_amount=total_amount,
            **request.data.get('shipping_details', {})
        )
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product_variant=cart_item.product_variant,
                quantity=cart_item.quantity,
                price=cart_item.product_variant.final_price
            )
        
        # Clear cart
        cart.items.all().delete()
        
        return Response({
            'order_id': str(order.id),
            'amount': int(total_amount * 100),
            'message': 'Order created successfully'
        })