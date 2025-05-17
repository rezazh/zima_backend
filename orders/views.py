from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from cart.models import CartItem
from users.models import Address
from .models import Order, OrderItem


@login_required
def checkout(request):
    """صفحه تکمیل سفارش"""
    cart_items = CartItem.objects.filter(user=request.user)
    addresses = Address.objects.filter(user=request.user)

    # بررسی خالی نبودن سبد خرید
    if not cart_items.exists():
        messages.error(request, 'سبد خرید شما خالی است.')
        return redirect('cart:summary')

    # محاسبه مجموع قیمت‌ها
    subtotal = sum(item.get_total_price() for item in cart_items)
    discount = sum(item.get_discount_amount() for item in cart_items)

    # محاسبه هزینه ارسال
    shipping_cost = 30000 if subtotal < 300000 else 0

    # محاسبه مبلغ نهایی
    total = subtotal - discount + shipping_cost

    cart_total = {
        'total_items': sum(item.quantity for item in cart_items),
        'subtotal': subtotal,
        'discount': discount,
        'shipping_cost': shipping_cost,
        'total': total
    }

    if request.method == 'POST':
        # دریافت اطلاعات سفارش
        address_id = request.POST.get('address_id')
        shipping_method = request.POST.get('shipping_method')
        payment_method = request.POST.get('payment_method')
        description = request.POST.get('description', '')

        # بررسی انتخاب آدرس
        if not address_id:
            messages.error(request, 'لطفاً یک آدرس انتخاب کنید.')
            return redirect('orders:checkout')

        address = get_object_or_404(Address, id=address_id, user=request.user)

        # محاسبه هزینه ارسال بر اساس روش ارسال
        if shipping_method == 'express':
            shipping_cost = 50000
        else:  # standard
            shipping_cost = 30000 if subtotal < 300000 else 0

        # ایجاد سفارش جدید
        order = Order.objects.create(
            user=request.user,
            address=address,
            shipping_method=shipping_method,
            payment_method=payment_method,
            description=description,
            subtotal=subtotal,
            discount=discount,
            shipping_cost=shipping_cost,
            total_price=subtotal - discount + shipping_cost
        )

        # ایجاد آیتم‌های سفارش
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                size=cart_item.size,
                color=cart_item.color,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
                discount=cart_item.discount
            )

        # خالی کردن سبد خرید
        cart_items.delete()

        # هدایت به صفحه پرداخت یا تأیید سفارش
        if payment_method == 'online':
            return redirect('orders:payment', order_id=order.id)
        else:  # cash
            order.status = 'confirmed'
            order.save()
            messages.success(request, 'سفارش شما با موفقیت ثبت شد.')
            return redirect('orders:confirmation', order_id=order.id)

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'addresses': addresses,
    }

    return render(request, 'orders/checkout.html', context)


@login_required
def payment(request, order_id):
    """صفحه پرداخت"""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # اگر سفارش قبلاً پرداخت شده باشد
    if order.status != 'pending':
        messages.warning(request, 'این سفارش قبلاً پرداخت شده است.')
        return redirect('orders:list')

    # در اینجا اتصال به درگاه پرداخت انجام می‌شود
    # ...

    # برای نمونه، فرض می‌کنیم پرداخت موفق بوده است
    if request.method == 'POST':
        order.status = 'paid'
        order.payment_date = timezone.now()
        order.save()

        messages.success(request, 'پرداخت با موفقیت انجام شد.')
        return redirect('orders:confirmation', order_id=order.id)

    return render(request, 'orders/payment.html', {'order': order})


@login_required
def order_confirmation(request, order_id):
    """صفحه تأیید سفارش"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/confirmation.html', {'order': order})


@login_required
def order_list(request):
    """لیست سفارشات کاربر"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/list.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    """جزئیات سفارش"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/detail.html', {'order': order})