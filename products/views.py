from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Avg, Count, Min, Max, Value, BooleanField, Sum
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import logging

from cart.models import WishlistItem, CartItem
from .models import Product, Category, Color, Size, ProductInventory, ProductImage, Review

logger = logging.getLogger(__name__)

def _apply_filters_and_sort(request, products_queryset):
    """اعمال فیلترها و مرتب‌سازی بر روی کوئری محصولات"""
    query = request.GET.get('q', '')
    categories_ids = request.GET.getlist('categories')
    sizes_ids = request.GET.getlist('sizes')
    colors_ids = request.GET.getlist('colors')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'newest')
    brands = request.GET.getlist('brand')

    if query:
        products_queryset = products_queryset.filter(
            Q(name__icontains=query) | Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(brand__icontains=brands)
        ).distinct()

    if categories_ids:
        products_queryset = products_queryset.filter(category__id__in=categories_ids).distinct()

    if sizes_ids:
        products_queryset = products_queryset.filter(inventories__size__id__in=sizes_ids).distinct()
    if colors_ids:
        products_queryset = products_queryset.filter(inventories__color__id__in=colors_ids).distinct()

    if min_price:
        try:
            min_price = float(min_price)
            products_queryset = products_queryset.filter(price__gte=min_price)
        except ValueError:
            pass

    if max_price:
        try:
            max_price = float(max_price)
            products_queryset = products_queryset.filter(price__lte=max_price)
        except ValueError:
            pass

    if brands:
        products_queryset = products_queryset.filter(brand__in=brands)

    # مرتب‌سازی
    if sort_by == 'newest':
        products_queryset = products_queryset.order_by('-created_at')
    elif sort_by == 'popular':
        products_queryset = products_queryset.annotate(sales_count=Count('total_sales')).order_by('-total_sales')
    elif sort_by == 'price_low':
        products_queryset = products_queryset.order_by('price')
    elif sort_by == 'price_high':
        products_queryset = products_queryset.order_by('-price')
    elif sort_by == 'rating':
        products_queryset = products_queryset.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    elif sort_by == 'discount':
        products_queryset = products_queryset.filter(discount_percent__gt=0).order_by('-discount_percent')

    return products_queryset, {
        'q': query,
        'categories': categories_ids,
        'sizes': sizes_ids,
        'colors': colors_ids,
        'min_price': min_price,
        'max_price': max_price,
        'brand': brands,
        'sort': sort_by,
    }


def product_list(request):
    """لیست همه محصولات"""
    products_queryset = Product.objects.filter(is_active=True).prefetch_related('images', 'inventories__color',
                                                                                'inventories__size')

    if request.user.is_authenticated:
        products_queryset = products_queryset.annotate(
            is_favorited=Count('wishlistitem', filter=Q(wishlistitem__user=request.user))
        )
    else:
        products_queryset = products_queryset.annotate(is_favorited=Value(0, output_field=BooleanField()))

    products_queryset, current_filters = _apply_filters_and_sort(request, products_queryset)

    # صفحه‌بندی
    paginator = Paginator(products_queryset, 9)
    page_number = request.GET.get('page')
    try:
        products = paginator.page(page_number)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    # دسته‌بندی‌ها
    all_categories = Category.objects.annotate(product_count=Count('products')).filter(product_count__gt=0)

    available_inventory = ProductInventory.objects.filter(
        product__in=products_queryset,
        quantity__gt=0
    )
    available_color_ids = available_inventory.values_list('color_id', flat=True).distinct()
    available_size_ids = available_inventory.values_list('size_id', flat=True).distinct()

    # دریافت آبجکت‌های رنگ و سایز موجود
    all_colors = Color.objects.filter(id__in=available_color_ids).order_by('name')
    all_sizes = Size.objects.filter(id__in=available_size_ids).order_by('name')

    all_brands = products_queryset.values_list('brand', flat=True).distinct().order_by('brand')

    # محدوده قیمت
    price_range_qs = Product.objects.filter(is_active=True)
    min_overall_price = price_range_qs.aggregate(min_price=Min('price'))['min_price']
    max_overall_price = price_range_qs.aggregate(max_price=Max('price'))['max_price']

    price_range = {
        'min_price': min_overall_price if min_overall_price is not None else 0,
        'max_price': max_overall_price if max_overall_price is not None else 10000000,
    }

    context = {
        'page_title': 'همه محصولات',
        'products': products,
        'results_count': products_queryset.count(),
        'all_categories': all_categories,
        'all_sizes': all_sizes,
        'all_colors': all_colors,
        'all_brands': all_brands,
        'price_range': price_range,
        'current_filters': current_filters,
    }
    return render(request, 'products/product_list.html', context)


def category_list(request, category_slug):
    """لیست محصولات یک دسته‌بندی خاص"""
    category = get_object_or_404(Category, slug=category_slug)
    products_queryset = Product.objects.filter(is_active=True).filter(
        Q(category=category) | Q(category__parent=category)
    ).prefetch_related('images')

    if request.user.is_authenticated:
        products_queryset = products_queryset.annotate(
            is_favorited=Count('wishlistitem', filter=Q(wishlistitem__user=request.user))
        )
    else:
        products_queryset = products_queryset.annotate(is_favorited=Value(0, output_field=BooleanField()))

    products_queryset, current_filters = _apply_filters_and_sort(request, products_queryset)

    # صفحه‌بندی
    paginator = Paginator(products_queryset, 9)
    page_number = request.GET.get('page')
    try:
        products = paginator.page(page_number)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    # زیردسته‌ها
    subcategories = category.children.annotate(product_count=Count('products')).filter(product_count__gt=0)

    available_inventory = ProductInventory.objects.filter(
        product__in=products_queryset,
        quantity__gt=0
    )
    available_color_ids = available_inventory.values_list('color_id', flat=True).distinct()
    available_size_ids = available_inventory.values_list('size_id', flat=True).distinct()

    # دریافت آبجکت‌های رنگ و سایز موجود
    all_colors = Color.objects.filter(id__in=available_color_ids).order_by('name')
    all_sizes = Size.objects.filter(id__in=available_size_ids).order_by('name')

    all_brands = products_queryset.values_list('brand', flat=True).distinct().order_by('brand')

    # محدوده قیمت برای این دسته‌بندی
    price_range_qs = Product.objects.filter(is_active=True, category=category)
    min_overall_price = price_range_qs.aggregate(min_price=Min('price'))['min_price']
    max_overall_price = price_range_qs.aggregate(max_price=Max('price'))['max_price']
    price_range = {
        'min_price': min_overall_price if min_overall_price is not None else 0,
        'max_price': max_overall_price if max_overall_price is not None else 10000000,
    }

    context = {
        'page_title': category.name,
        'products': products,
        'category': category,
        'subcategories': subcategories,
        'results_count': products_queryset.count(),
        'all_sizes': all_sizes,
        'all_colors': all_colors,
        'all_brands': all_brands,
        'price_range': price_range,
        'current_filters': current_filters,
    }
    return render(request, 'products/category_detail.html', context)


def search_results(request):
    """نتایج جستجو"""
    products_queryset = Product.objects.filter(is_active=True).prefetch_related('images')

    if request.user.is_authenticated:
        products_queryset = products_queryset.annotate(
            is_favorited=Count('wishlistitem', filter=Q(wishlistitem__user=request.user))
        )
    else:
        products_queryset = products_queryset.annotate(is_favorited=Value(0, output_field=BooleanField()))

    products_queryset, current_filters = _apply_filters_and_sort(request, products_queryset)
    query = request.GET.get('q', '')

    # صفحه‌بندی
    paginator = Paginator(products_queryset, 9)
    page_number = request.GET.get('page')
    try:
        products = paginator.page(page_number)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    # دسته‌بندی‌ها
    all_categories = Category.objects.annotate(product_count=Count('products')).filter(product_count__gt=0)

    available_inventory = ProductInventory.objects.filter(
        product__in=products_queryset,
        quantity__gt=0
    )
    available_color_ids = available_inventory.values_list('color_id', flat=True).distinct()
    available_size_ids = available_inventory.values_list('size_id', flat=True).distinct()

    # دریافت آبجکت‌های رنگ و سایز موجود
    all_colors = Color.objects.filter(id__in=available_color_ids).order_by('name')
    all_sizes = Size.objects.filter(id__in=available_size_ids).order_by('name')

    all_brands = products_queryset.values_list('brand', flat=True).distinct().order_by('brand')

    # محدوده قیمت
    price_range_qs = Product.objects.filter(is_active=True)
    min_overall_price = price_range_qs.aggregate(min_price=Min('price'))['min_price']
    max_overall_price = price_range_qs.aggregate(max_price=Max('price'))['max_price']
    price_range = {
        'min_price': min_overall_price if min_overall_price is not None else 0,
        'max_price': max_overall_price if max_overall_price is not None else 10000000,
    }

    context = {
        'page_title': f'نتایج جستجو برای: "{query}"',
        'query': query,
        'products': products,
        'results_count': products_queryset.count(),
        'all_categories': all_categories,
        'all_sizes': all_sizes,
        'all_colors': all_colors,
        'all_brands': all_brands,
        'price_range': price_range,
        'current_filters': current_filters,
    }
    return render(request, 'products/search_results.html', context)


def product_detail(request, product_id):
    """نمایش جزئیات محصول"""
    product = get_object_or_404(Product, id=product_id, is_active=True)

    # دریافت موجودی‌های محصول با رنگ و سایز
    inventories = ProductInventory.objects.filter(
        product=product,
        quantity__gt=0
    ).select_related('color', 'size')

    # محاسبه کل موجودی
    total_stock = sum(inv.quantity for inv in inventories)

    # دریافت رنگ‌ها و سایزهای موجود
    available_colors = Color.objects.filter(
        id__in=inventories.values_list('color_id', flat=True).distinct()
    ).distinct()

    available_sizes = Size.objects.filter(
        id__in=inventories.values_list('size_id', flat=True).distinct()
    ).distinct()

    # ایجاد mapping برای JavaScript
    inventory_mapping = {}
    for inv in inventories:
        color_id = str(inv.color.id) if inv.color else 'null'
        size_id = str(inv.size.id) if inv.size else 'null'

        if color_id not in inventory_mapping:
            inventory_mapping[color_id] = {}

        inventory_mapping[color_id][size_id] = {
            'quantity': inv.quantity,
            'size_name': inv.size.name if inv.size else '',
            'color_name': inv.color.name if inv.color else ''
        }

    # محصولات مشابه
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:8]

    # اگر محصولات مشابه کم بود، از دسته‌های مرتبط هم بگیر
    if related_products.count() < 4:
        related_products = Product.objects.filter(
            Q(category=product.category) | Q(brand=product.brand),
            is_active=True
        ).exclude(id=product.id)[:8]

    # بررسی اینکه کاربر این محصول را خریداری کرده یا نه
    has_purchased = False
    if request.user.is_authenticated:
        # فرض می‌کنیم مدل Order و OrderItem دارید
        # has_purchased = OrderItem.objects.filter(
        #     order__user=request.user,
        #     product=product,
        #     order__status='completed'
        # ).exists()
        pass

    context = {
        'product': product,
        'related_products': related_products,
        'available_colors': available_colors,
        'available_sizes': available_sizes,
        'total_stock': total_stock,
        'inventory_mapping': json.dumps(inventory_mapping),
        'has_purchased': has_purchased,
    }

    return render(request, 'products/product_detail.html', context)


@require_POST
def add_review(request, product_id):
    """افزودن نظر به محصول"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'برای ثبت نظر ابتدا وارد حساب کاربری خود شوید.',
            'redirect': '/accounts/login/'
        })

    product = get_object_or_404(Product, id=product_id)

    # بررسی اینکه کاربر این محصول را خریداری کرده یا نه
    # has_purchased = OrderItem.objects.filter(
    #     order__user=request.user,
    #     product=product,
    #     order__status='completed'
    # ).exists()

    # فعلاً این بررسی را غیرفعال می‌کنیم
    has_purchased = True

    if not has_purchased:
        return JsonResponse({
            'success': False,
            'message': 'فقط کاربرانی که این محصول را خریداری کرده‌اند می‌توانند نظر ثبت کنند.'
        })

    try:
        rating = int(request.POST.get('rating', 5))
        comment = request.POST.get('comment', '')

        if not comment.strip():
            return JsonResponse({
                'success': False,
                'message': 'لطفاً متن نظر خود را وارد کنید.'
            })

        # بررسی اینکه کاربر قبلاً نظر داده یا نه
        existing_review, created = Review.objects.get_or_create(
            product=product,
            user=request.user,
            defaults={'rating': rating, 'comment': comment}
        )

        if not created:
            existing_review.rating = rating
            existing_review.comment = comment
            existing_review.save()
            message = 'نظر شما با موفقیت به‌روزرسانی شد.'
        else:
            message = 'نظر شما با موفقیت ثبت شد.'

        return JsonResponse({
            'success': True,
            'message': message
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'خطا در ثبت نظر. لطفاً دوباره تلاش کنید.'
        })


def quick_view(request, product_id):
    try:
        logger.info(f"Quick view requested for product {product_id}")

        # دریافت محصول
        product = get_object_or_404(Product, id=product_id, is_active=True)
        logger.info(f"Product found: {product.name}")

        # دریافت موجودی‌ها
        inventories = ProductInventory.objects.select_related('color', 'size').filter(
            product=product,
            quantity__gt=0  # فقط موجودی‌های بیشتر از صفر
        ).order_by('color__name', 'size__name')

        logger.info(f"Found {inventories.count()} inventory records")

        # محاسبه موجودی کل - استفاده از property total_stock
        total_stock = product.total_stock

        # ساخت inventory mapping و جمع‌آوری رنگ‌ها و سایزها
        inventory_mapping = {}
        colors_dict = {}
        sizes_dict = {}

        for inv in inventories:
            if not inv.color or not inv.size:
                continue  # Skip if color or size is None

            color_key = str(inv.color.id)
            size_key = str(inv.size.id)

            # اضافه کردن به inventory mapping
            if color_key not in inventory_mapping:
                inventory_mapping[color_key] = {}

            inventory_mapping[color_key][size_key] = {
                'quantity': inv.quantity,
                'color_name': inv.color.name,
                'color_hex': getattr(inv.color, 'hex_code', '#CCCCCC') or '#CCCCCC',
                'size_name': inv.size.name
            }

            # جمع‌آوری رنگ‌ها و سایزها
            if inv.color.id not in colors_dict:
                colors_dict[inv.color.id] = {
                    'id': inv.color.id,
                    'name': inv.color.name,
                    'hex_code': getattr(inv.color, 'hex_code', '#CCCCCC') or '#CCCCCC'
                }

            if inv.size.id not in sizes_dict:
                sizes_dict[inv.size.id] = {
                    'id': inv.size.id,
                    'name': inv.size.name
                }

        # تبدیل dict به list و مرتب‌سازی
        available_colors = list(colors_dict.values())
        available_sizes = list(sizes_dict.values())

        available_colors.sort(key=lambda x: x['name'])
        available_sizes.sort(key=lambda x: x['name'])

        logger.info(f"Available colors: {len(available_colors)}")
        logger.info(f"Available sizes: {len(available_sizes)}")
        logger.info(f"Total stock: {total_stock}")

        # بررسی وضعیت علاقه‌مندی
        is_favorited = False
        if request.user.is_authenticated:
            try:
                from cart.models import WishlistItem
                is_favorited = WishlistItem.objects.filter(
                    user=request.user,
                    product=product
                ).exists()
            except Exception:
                is_favorited = False

        context = {
            'product': product,
            'total_stock': total_stock,  # استفاده از total_stock
            'available_colors': available_colors,
            'available_sizes': available_sizes,
            'inventory_mapping': json.dumps(inventory_mapping, ensure_ascii=False, separators=(',', ':')),
            'is_favorited': is_favorited,
        }

        logger.info("Context prepared successfully, rendering template")
        return render(request, 'products/quick_view_modal_content.html', context)

    except Product.DoesNotExist:
        logger.error(f"Product with id {product_id} not found")
        return JsonResponse({
            'error': 'محصول مورد نظر یافت نشد'
        }, status=404)

    except Exception as e:
        logger.error(f"Error in quick_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': f'خطا در بارگذاری اطلاعات محصول: {str(e)}'
        }, status=500)
@require_POST
@csrf_exempt
def toggle_wishlist(request):
    """اضافه/حذف محصول از علاقه‌مندی‌ها"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'برای این عمل باید وارد شوید'
        })

    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        product = get_object_or_404(Product, id=product_id)

        wishlist_item, created = WishlistItem.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            wishlist_item.delete()
            is_favorited = False
        else:
            is_favorited = True

        return JsonResponse({
            'success': True,
            'is_favorited': is_favorited
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'خطا در عملیات'
        })


@require_POST
def add_to_cart(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        color_id = data.get('color_id')
        size_id = data.get('size_id')

        product = Product.objects.get(id=product_id, is_active=True)

        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'لطفاً ابتدا وارد حساب کاربری خود شوید.',
                'redirect': '/users/login/'
            })

        # تعیین نام رنگ و سایز
        color_name = None
        size_name = None
        inventory = None

        # پیدا کردن inventory مناسب
        if color_id and size_id:
            try:
                color = Color.objects.get(id=color_id)
                size = Size.objects.get(id=size_id)
                color_name = color.name
                size_name = size.name

                # پیدا کردن inventory
                inventory = ProductInventory.objects.get(
                    product=product,
                    color=color,
                    size=size
                )

                # بررسی موجودی
                if quantity > inventory.quantity:
                    return JsonResponse({
                        'success': False,
                        'error': f'تنها {inventory.quantity} عدد از این ترکیب موجود است.'
                    })

            except Color.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'رنگ انتخاب شده یافت نشد.'})
            except Size.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'سایز انتخاب شده یافت نشد.'})
            except ProductInventory.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'این ترکیب رنگ و سایز موجود نیست.'})

        elif color_id:
            try:
                color = Color.objects.get(id=color_id)
                color_name = color.name
            except Color.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'رنگ انتخاب شده یافت نشد.'})

        elif size_id:
            try:
                size = Size.objects.get(id=size_id)
                size_name = size.name
            except Size.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'سایز انتخاب شده یافت نشد.'})

        # بررسی موجودی کل محصول اگر inventory خاص نداریم
        if not inventory:
            total_stock = product.total_stock  # استفاده از property total_stock
            if quantity > total_stock:
                return JsonResponse({
                    'success': False,
                    'error': f'تنها {total_stock} عدد از این محصول موجود است.'
                })

        # ایجاد یا به‌روزرسانی CartItem
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            color=color_name or '',
            size=size_name or '',
            defaults={
                'quantity': quantity,
                'inventory': inventory
            }
        )

        if not created:
            # بررسی موجودی برای quantity جدید
            new_quantity = cart_item.quantity + quantity
            max_quantity = inventory.quantity if inventory else product.total_stock

            if new_quantity > max_quantity:
                return JsonResponse({
                    'success': False,
                    'error': f'تنها {max_quantity} عدد از این محصول موجود است. شما {cart_item.quantity} عدد در سبد دارید.'
                })

            cart_item.quantity = new_quantity
            cart_item.save()

        # محاسبه تعداد کل آیتم‌های سبد
        cart_items_count = CartItem.objects.filter(user=request.user).count()

        return JsonResponse({
            'success': True,
            'message': 'محصول با موفقیت به سبد خرید اضافه شد.',
            'cart_items_count': cart_items_count
        })

    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'محصول یافت نشد.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'خطا در افزودن به سبد خرید: {str(e)}'})