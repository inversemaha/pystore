from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import *

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name', 'phone_number', 'password', 'password_confirm')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = CustomUser.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if user and user.is_active:
                attrs['user'] = user
                return attrs
            raise serializers.ValidationError('Invalid credentials')
        raise serializers.ValidationError('Email and password required')

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = '__all__'

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = '__all__'

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'alt_text', 'is_primary')

class ProductVariantSerializer(serializers.ModelSerializer):
    color = ColorSerializer(read_only=True)
    size = SizeSerializer(read_only=True)
    final_price = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductVariant
        fields = ('id', 'color', 'size', 'sku', 'stock_quantity', 'additional_price', 'final_price')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'image')

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    discounted_price = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'description', 'category', 'base_price', 
                 'discount_percentage', 'discounted_price', 'is_featured', 'images', 
                 'variants', 'meta_title', 'meta_description', 'created_at')

class CartItemSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantSerializer(read_only=True)
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = CartItem
        fields = ('id', 'product_variant', 'quantity', 'total_price')

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Cart
        fields = ('id', 'items', 'created_at', 'updated_at')

class OrderItemSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantSerializer(read_only=True)
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = OrderItem
        fields = ('id', 'product_variant', 'quantity', 'price', 'total_price')

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ('id', 'order_number', 'status', 'payment_status', 'shipping_name', 
                 'shipping_email', 'shipping_phone', 'shipping_address', 'shipping_city', 
                 'shipping_state', 'shipping_pincode', 'subtotal', 'shipping_cost', 
                 'tax_amount', 'total_amount', 'items', 'created_at', 'updated_at')