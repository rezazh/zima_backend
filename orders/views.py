from django.db import transaction
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view

from .models import Order, CartItem, OrderStatusHistory
from .serializers import OrderSerializer, CartItemSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import OrderSerializer

from zarinpal import ZarinPal
from .models import Payment




class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart_items = CartItem.objects.filter(user=request.user)
        serializer = CartItemSerializer(cart_items, many=True)
        return Response(serializer.data)

class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "Item removed from cart."}, status=status.HTTP_204_NO_CONTENT)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        cart_items = CartItem.objects.filter(user=user)

        if not cart_items.exists():
            return Response({"error": "Your cart is empty!"}, status=400)

        with transaction.atomic():
            orders = []
            for item in cart_items:
                if item.product.stock < item.quantity:
                    return Response({"error": f"Not enough stock for {item.product.name}"}, status=400)

                order = Order.objects.create(
                    user=user,
                    product=item.product,
                    quantity=item.quantity,
                    total_price=item.total_price,
                    status='PENDING'
                )
                orders.append(order)

                item.product.stock -= item.quantity
                item.product.save()

            cart_items.delete()

        return Response({"message": "Order placed successfully!", "orders": [order.id for order in orders]})



class OrderHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)



class PaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        order = Order.objects.get(id=order_id, user=request.user)
        if order.status != 'PENDING':
            return Response({"error": "Order is not pending"}, status=400)

        zarinpal = ZarinPal(merchant_id='YOUR_MERCHANT_ID')
        amount = order.total_price
        callback_url = 'http://127.0.0.1:8000/api/orders/payment/callback/'
        description = f"Payment for Order {order.id}"

        result = zarinpal.request_payment(amount, callback_url, description)
        if result['status'] == 100:
            Payment.objects.create(order=order, amount=amount, transaction_id=result['authority'])
            return Response({"url": result['url']})
        return Response({"error": "Payment request failed"}, status=400)


@api_view(['PATCH'])
def update_order_status(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    new_status = request.data.get('status')

    if new_status not in dict(Order.STATUS_CHOICES):
        return Response({"error": "Invalid status"}, status=400)

    order.status = new_status
    order.save()
    return Response({"message": f"Order status updated to {new_status}"})


@api_view(['PATCH'])
def update_order_status(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    new_status = request.data.get('status')

    if new_status not in dict(Order.STATUS_CHOICES):
        return Response({"error": "Invalid status"}, status=400)

    old_status = order.status
    order.status = new_status
    order.save()

    OrderStatusHistory.objects.create(order=order, old_status=old_status, new_status=new_status)

    # send_order_status_email(order)

    return Response({"message": f"Order status updated to {new_status}"})