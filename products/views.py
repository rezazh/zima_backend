from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Min, Max
from django.contrib import messages
from .models import Product, Category, Review, ProductInventory, Size, Color


def product_list(request):
    """نمایش لیست محصولات با امکان فیلتر و مرتب‌سازی"""
    products = Product.objects.all()

    # فیلتر بر اساس دسته‌بندی
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # فیلتر بر اساس جستجو
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(brand__icontains=search_query)
        )

    # فیلتر بر اساس قیمت
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')

    if price_min:
        products = products.filter(price__gte=price_min)
    if price_max:
        products = products.filter(price__lte=price_max)

    # فیلتر بر اساس سایز، رنگ و برند
    size = request.GET.get('size')
    color = request.GET.get('color')
    brand = request.GET.get('brand')

    if size:
        products = products.filter(sizes__icontains=size)
    if color:
        products = products.filter(colors__icontains=color)
    if brand:
        products = products.filter(brand__icontains=brand)

    # مرتب‌سازی
    sort = request.GET.get('sort', 'newest')
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'popular':
        products = products.order_by('-views')
    else:  # newest (default)
        products = products.order_by('-created_at')

    # تعریف گزینه‌های فیلتر (خارج از شرط)
    filter_options = {
        'sizes': ['S', 'M', 'L', 'XL', 'XXL'],
        'colors': [
            'سفید', 'مشکی', 'خاکستری', 'نقره‌ای',
            'قرمز', 'زرشکی', 'صورتی', 'گلبهی',
            'نارنجی', 'هلویی', 'طلایی', 'زرد', 'لیمویی',
            'سبز', 'سبز لجنی', 'سبز یشمی', 'سبز زیتونی',
            'آبی', 'آبی آسمانی', 'آبی نفتی', 'فیروزه‌ای',
            'بنفش', 'یاسی', 'ارغوانی',
            'قهوه‌ای', 'کرم', 'بژ', 'شکلاتی', 'عنابی',
            'مسی', 'برنزی', 'سرمه‌ای', 'کالباسی', 'نباتی', 'آجری'
        ],
        'brands': Product.objects.values_list('brand', flat=True).distinct(),
    }

    # صفحه‌بندی
    paginator = Paginator(products, 12)  # 12 محصول در هر صفحه
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'filter_options': filter_options,
        'page_title': 'همه محصولات',
    }

    return render(request, 'products/product_list.html', context)


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)

    # دریافت رنگ‌ها و سایزهای موجود برای این محصول
    available_inventories = ProductInventory.objects.filter(product=product, quantity__gt=0)

    # استخراج رنگ‌های منحصر به فرد
    available_colors = []
    for inventory in available_inventories:
        if inventory.color not in available_colors:
            available_colors.append(inventory.color)

    # استخراج سایزهای منحصر به فرد
    available_sizes = []
    for inventory in available_inventories:
        if inventory.size not in available_sizes:
            available_sizes.append(inventory.size)
    inventories_data = [inventory.to_dict() for inventory in available_inventories]
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]
    context = {
        'product': product,
        'available_colors': available_colors,
        'available_sizes': available_sizes,
        'inventories': inventories_data,
        'related_products': related_products,

    }
    return render(request, 'products/product_detail.html', context)


def category_products(request, category_slug):
    """نمایش محصولات یک دسته‌بندی خاص"""
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category)

    # مرتب‌سازی
    sort = request.GET.get('sort', 'newest')
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'popular':
        products = products.annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')
    else:  # newest
        products = products.order_by('-created_at')

    # صفحه‌بندی
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'category': category,
        'page_title': f'محصولات {category.name}',
    }

    return render(request, 'products/product_list.html', context)


def men_products(request):
    """نمایش محصولات مردانه"""
    men_category = get_object_or_404(Category, slug='men')
    products = Product.objects.filter(category=men_category)

    # مرتب‌سازی و فیلترها مشابه product_list

    # صفحه‌بندی
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'page_title': 'محصولات مردانه',
    }

    return render(request, 'products/product_list.html', context)


def women_products(request):
    """نمایش محصولات زنانه"""
    women_category = get_object_or_404(Category, slug='women')
    products = Product.objects.filter(category=women_category)

    # مرتب‌سازی و فیلترها مشابه product_list

    # صفحه‌بندی
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'page_title': 'محصولات زنانه',
    }

    return render(request, 'products/product_list.html', context)


def featured_products(request):
    """نمایش محصولات ویژه"""
    products = Product.objects.filter(is_featured=True)

    # مرتب‌سازی و فیلترها مشابه product_list

    # صفحه‌بندی
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'page_title': 'محصولات ویژه',
    }

    return render(request, 'products/product_list.html', context)


def latest_products(request):
    """نمایش جدیدترین محصولات"""
    products = Product.objects.order_by('-created_at')

    # صفحه‌بندی
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'page_title': 'جدیدترین محصولات',
    }

    return render(request, 'products/product_list.html', context)


@login_required
def add_review(request, product_id):
    """افزودن نظر برای محصول"""
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        # بررسی اینکه کاربر قبلاً نظر داده یا نه
        if Review.objects.filter(product=product, user=request.user).exists():
            messages.error(request, 'شما قبلاً برای این محصول نظر ثبت کرده‌اید.')
        else:
            Review.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                comment=comment
            )
            messages.success(request, 'نظر شما با موفقیت ثبت شد.')

    return redirect('products:detail', product_id=product_id)


def category_detail(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    subcategories = Category.objects.filter(parent=category, is_active=True)

    if subcategories.exists():
        category_ids = [category.id] + list(subcategories.values_list('id', flat=True))
        all_products = Product.objects.filter(category_id__in=category_ids, is_active=True)
    else:
        all_products = Product.objects.filter(category=category, is_active=True)

    all_brands = list(all_products.values_list('brand', flat=True).distinct().order_by('brand'))

    size_objects = Size.objects.filter(
        productinventory__product__in=all_products,
        productinventory__quantity__gt=0
    ).distinct().order_by('name')
    all_sizes = [size.name for size in size_objects]

    color_objects = Color.objects.filter(
        productinventory__product__in=all_products,
        productinventory__quantity__gt=0
    ).distinct().order_by('name')
    all_colors = [color.name for color in color_objects]

    products = all_products

    brand = request.GET.get('brand')
    if brand and brand != 'none':
        products = products.filter(brand__iexact=brand)

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if min_price:
        try:
            products = products.filter(price__gte=int(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            products = products.filter(price__lte=int(max_price))
        except ValueError:
            pass

    size = request.GET.get('size')
    color = request.GET.get('color')

    if size and size != 'none':
        products = products.filter(
            inventories__size__name=size,
            inventories__quantity__gt=0
        ).distinct()

    if color and color != 'none':
        products = products.filter(
            inventories__color__name=color,
            inventories__quantity__gt=0
        ).distinct()

    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'popular':
        products = products.order_by('-total_sales')
    else:  # newest
        products = products.order_by('-created_at')

    products = products[:12]  # یا استفاده از Paginator

    context = {
        'category': category,
        'subcategories': subcategories,
        'products': products,
        'all_brands': all_brands,
        'all_sizes': all_sizes,
        'all_colors': all_colors,
        'price_range': all_products.aggregate(min_price=Min('price'), max_price=Max('price')),
        'current_filters': {
            'brand': brand if brand and brand != 'none' else None,
            'size': size if size and size != 'none' else None,
            'color': color if color and color != 'none' else None,
            'min_price': min_price,
            'max_price': max_price,
            'sort': sort_by
        },
        'filters_applied': any([
            brand and brand != 'none',
            size and size != 'none',
            color and color != 'none',
            min_price,
            max_price
        ])
    }

    return render(request, 'products/category_detail.html', context)


def search_products(request):
    query = request.GET.get('q', '')
    if query:
        # جستجو در نام، توضیحات و برند محصولات
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query),
            is_active=True
        ).distinct()
    else:
        products = Product.objects.none()

    context = {
        'products': products,
        'query': query
    }

    return render(request, 'products/search_results.html', context)