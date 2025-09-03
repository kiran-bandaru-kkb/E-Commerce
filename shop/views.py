from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import F, Sum, ExpressionWrapper, DecimalField
from .models import Category, Product, Cart, CartItem, Order, OrderItem
from .permissions import IsAdminOrOwnerOrReadOnly, IsOwnerOrAdmin
from .serializers import CategorySerializer, ProductSerializer, CartSerializer, CartItemSerializer, OrderSerializer, OrderItemSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)  # auto-assign creator


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_admin:
            return Cart.objects.all()
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only items from the current user's cart
        return CartItem.objects.filter(cart__user=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_admin:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def place(self, request):
        user = request.user
        cart = user.cart
        items = cart.items.all()

        if not items:
            return Response({"error": "Cart is empty"}, status=400)

        with transaction.atomic():
            total_price = (
                    items.annotate(
                        line_total=ExpressionWrapper(F('product__price') * F('quantity'), output_field=DecimalField())
                    )
                    .aggregate(total=Sum('line_total'))['total'] or 0
            )

            order = Order.objects.create(
                user=user,
                total_price=total_price,
                status="pending"
            )
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
            cart.items.all().delete()  # empty cart after order

        return Response({"message": "Order placed successfully", "order_id": order.id})


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_admin:
            return OrderItem.objects.all()
        return OrderItem.objects.filter(order__user=self.request.user)

