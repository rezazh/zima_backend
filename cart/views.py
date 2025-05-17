from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from products.models import Product
from .models import CartItem, Coupon
from django.utils import timezone


@login_required
def cart_summary(request):
    """نمایش سبد خرید"""
    cart_items = CartItem.objects.filter(user=request.user)

    # محاسبه مجموع قیمت‌ها
    subtotal = sum(item.get_total_price() for item in cart_items)
    discount = sum(item.get_discount_amount() for item in cart_items)

    # محاسبه هزینه ارسال
    shipping_cost = 30000 if subtotal < 300000 and subtotal > 0 else 0

    # محاسبه مبلغ نهایی
    total = subtotal - discount + shipping_cost

    cart_total = {
        'total_items': sum(item.quantity for item in cart_items),
        'subtotal': subtotal,
        'discount': discount,
        'shipping_cost': shipping_cost,
        'total': total
    }

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total
    }

    return render(request, 'cart/summary.html', context)


@login_required
def add_to_cart(request, product_id):
    """افزودن محصول به سبد خرید"""
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        size = request.POST.get('size')
        color = request.POST.get('color')
        quantity = int(request.POST.get('quantity', 1))

        # بررسی موجودی کالا
        if product.stock < quantity:
            messages.error(request, 'موجودی کالا کافی نیست.')
            return redirect('products:detail', product_id=product_id)

        # بررسی وجود محصول مشابه در سبد خرید
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            size=size,
            color=color,
            defaults={'quantity': quantity}
        )

        # اگر محصول مشابه وجود داشته، تعداد را افزایش می‌دهیم
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        messages.success(request, 'محصول با موفقیت به سبد خرید اضافه شد.')

    return redirect('cart:summary')


@login_required
def update_cart(request, item_id):
    """بروزرسانی تعداد محصول در سبد خرید"""
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'increase':
            # بررسی موجودی کالا
            if cart_item.quantity < cart_item.product.stock:
                cart_item.quantity += 1
                cart_item.save()
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()

    return redirect('cart:summary')


@login_required
def remove_from_cart(request, item_id):
    """حذف محصول از سبد خرید"""
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)

    if request.method == 'POST':
        cart_item.delete()
        messages.success(request, 'محصول از سبد خرید حذف شد.')

    return redirect('cart:summary')


@login_required
def clear_cart(request):
    """خالی کردن سبد خرید"""
    if request.method == 'POST':
        CartItem.objects.filter(user=request.user).delete()
        messages.success(request, 'سبد خرید خالی شد.')

    return redirect('cart:summary')


@login_required
def apply_coupon(request):
    """اعمال کد تخفیف"""
    if request.method == 'POST':
        code = request.POST.get('code')

        try:
            coupon = Coupon.objects.get(
                code=code,
                valid_from__lte=timezone.now(),
                valid_to__gte=timezone.now(),
                active=True
            )

            # بررسی اینکه کاربر قبلاً از این کد تخفیف استفاده کرده یا نه
            if coupon.users.filter(id=request.user.id).exists():
                messages.error(request, 'شما قبلاً از این کد تخفیف استفاده کرده‌اید.')
            else:
                # اعمال تخفیف
                cart_items = CartItem.objects.filter(user=request.user)

                for item in cart_items:
                    item.discount = coupon.discount_percent
                    item.save()

                # ثبت استفاده کاربر از کد تخفیف
                coupon.users.add(request.user)

                messages.success(request, f'کد تخفیف {coupon.discount_percent}% با موفقیت اعمال شد.')

        except Coupon.DoesNotExist:
            messages.error(request, 'کد تخفیف نامعتبر است.')

    return redirect('cart:summary')