from collections.abc import Sized

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
import json
from products.models import Product, ProductInventory, Color, Size
from users.models import Favorite
from .models import CartItem, Coupon
from django.utils import timezone


@login_required
def cart_summary(request):
    """نمایش سبد خرید - تغییر نام از cart_summary به cart برای همخوانی با template"""
    cart_items = CartItem.objects.filter(user=request.user)

    # محاسبه مجموع قیمت‌ها
    original_subtotal = sum(item.get_original_total_price() for item in cart_items)  # قیمت اصلی
    subtotal = sum(item.get_total_price() for item in cart_items)  # قیمت با تخفیف محصولات
    product_discount = sum(item.get_product_discount_amount() for item in cart_items)  # تخفیف محصولات
    coupon_discount = sum(item.get_coupon_discount_amount() for item in cart_items)  # تخفیف کوپن
    total_discount = product_discount + coupon_discount  # مجموع تخفیفات

    # هزینه حمل و نقل
    shipping_cost = 30000 if subtotal < 300000 and subtotal > 0 else 0

    # قیمت نهایی
    total = subtotal - coupon_discount + shipping_cost

    # محاسبه مبلغ باقی‌مانده برای ارسال رایگان
    free_shipping_remaining = max(0, 300000 - subtotal) if subtotal > 0 and subtotal < 300000 else 0

    # بررسی کوپن اعمال شده
    applied_coupon = None
    if cart_items.exists() and cart_items.first().discount > 0:
        # پیدا کردن کوپن اعمال شده
        try:
            applied_coupon = Coupon.objects.filter(
                discount_percent=cart_items.first().discount,
                users=request.user
            ).first()
        except:
            applied_coupon = None

    cart_total = {
        'total_items': sum(item.quantity for item in cart_items),
        'original_subtotal': original_subtotal,  # قیمت اصلی
        'subtotal': subtotal,  # قیمت با تخفیف محصولات
        'product_discount': product_discount,  # تخفیف محصولات
        'coupon_discount': coupon_discount,  # تخفیف کوپن
        'total_discount': total_discount,  # مجموع تخفیفات
        'shipping_cost': shipping_cost,
        'total': total,  # قیمت نهایی
        'total_savings': total_discount,  # مجموع صرفه‌جویی
        'free_shipping_remaining': free_shipping_remaining,  # مبلغ باقی‌مانده برای ارسال رایگان
        'tax_amount': 0,  # مالیات (در صورت نیاز)
    }

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'applied_coupon': applied_coupon,
    }

    # تغییر template به cart.html
    return render(request, 'cart/cart.html', context)





@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)

    if request.method == 'POST':
        # بررسی درخواست Ajax برای تغییر مستقیم quantity
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                action = data.get('action')

                if action == 'set_quantity':
                    new_quantity = int(data.get('quantity', 1))
                    if 1 <= new_quantity <= 10:  # محدودیت quantity
                        # بررسی موجودی
                        max_quantity = cart_item.inventory.quantity if cart_item.inventory else cart_item.product.stock
                        if new_quantity <= max_quantity:
                            cart_item.quantity = new_quantity
                            cart_item.save()
                            return JsonResponse({'success': True})
                        else:
                            return JsonResponse({'success': False, 'error': 'موجودی کافی نیست'})
                    else:
                        return JsonResponse({'success': False, 'error': 'تعداد نامعتبر'})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

        # درخواست معمولی form
        action = request.POST.get('action')

        if action == 'increase':
            max_quantity = cart_item.inventory.quantity if cart_item.inventory else cart_item.product.stock
            if cart_item.quantity < max_quantity:
                cart_item.quantity += 1
                cart_item.save()
                messages.success(request, 'تعداد محصول افزایش یافت.')
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
                messages.success(request, 'تعداد محصول کاهش یافت.')
            else:
                cart_item.delete()
                messages.success(request, 'محصول از سبد خرید حذف شد.')

    return redirect('cart:cart')


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)

    if request.method == 'POST':
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f'محصول "{product_name}" از سبد خرید حذف شد.')

    return redirect('cart:cart')


@login_required
def clear_cart(request):
    if request.method == 'POST':
        cart_count = CartItem.objects.filter(user=request.user).count()
        CartItem.objects.filter(user=request.user).delete()
        messages.success(request, f'{cart_count} محصول از سبد خرید حذف شد.')

    return redirect('cart:cart')


@login_required
def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()

        if not code:
            messages.error(request, 'لطفاً کد تخفیف را وارد کنید.')
            return redirect('cart:cart')

        try:
            coupon = Coupon.objects.get(
                code=code,
                valid_from__lte=timezone.now(),
                valid_to__gte=timezone.now(),
                active=True
            )

            # بررسی استفاده قبلی
            if coupon.users.filter(id=request.user.id).exists():
                messages.error(request, 'شما قبلاً از این کد تخفیف استفاده کرده‌اید.')
                return redirect('cart:cart')

            # بررسی حداقل مبلغ خرید
            cart_items = CartItem.objects.filter(user=request.user)
            if not cart_items.exists():
                messages.error(request, 'سبد خرید شما خالی است.')
                return redirect('cart:cart')

            subtotal = sum(item.get_total_price() for item in cart_items)

            if subtotal < coupon.min_purchase:
                messages.error(request, f'حداقل مبلغ خرید برای این کد تخفیف {coupon.min_purchase:,} تومان است.')
                return redirect('cart:cart')

            # اعمال کد تخفیف به تمام آیتم‌های سبد
            for item in cart_items:
                item.discount = coupon.discount_percent
                item.save()

            coupon.users.add(request.user)
            messages.success(request, f'کد تخفیف {coupon.discount_percent}% با موفقیت اعمال شد.')

        except Coupon.DoesNotExist:
            messages.error(request, 'کد تخفیف نامعتبر یا منقضی شده است.')

    return redirect('cart:cart')


@login_required
def remove_coupon(request):
    """حذف کد تخفیف اعمال شده"""
    if request.method == 'POST':
        cart_items = CartItem.objects.filter(user=request.user)

        if cart_items.exists():
            # حذف تخفیف از تمام آیتم‌ها
            for item in cart_items:
                if item.discount > 0:
                    item.discount = 0
                    item.save()

            messages.success(request, 'کد تخفیف با موفقیت حذف شد.')
        else:
            messages.error(request, 'سبد خرید شما خالی است.')

    return redirect('cart:cart')


@login_required
def save_for_later(request, item_id):
    """ذخیره محصول برای بعد (انتقال به wishlist)"""
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)

        try:

            favorite_item, created = Favorite.objects.get_or_create(  # ✅ تغییر از WishlistItem به Favorite
                user=request.user,
                product=cart_item.product
            )

            if created:
                # حذف از سبد خرید
                product_name = cart_item.product.name
                cart_item.delete()

                if request.content_type == 'application/json':
                    return JsonResponse({
                        'success': True,
                        'message': f'محصول "{product_name}" برای بعد ذخیره شد.'
                    })
                else:
                    messages.success(request, f'محصول "{product_name}" برای بعد ذخیره شد.')
            else:
                if request.content_type == 'application/json':
                    return JsonResponse({
                        'success': False,
                        'message': 'این محصول قبلاً در لیست علاقه‌مندی‌های شما موجود است.'
                    })
                else:
                    messages.info(request, 'این محصول قبلاً در لیست علاقه‌مندی‌های شما موجود است.')

        except Exception as e:
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'message': 'خطا در ذخیره محصول.'
                })
            else:
                messages.error(request, 'خطا در ذخیره محصول.')

    return redirect('cart:cart')