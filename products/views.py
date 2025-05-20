from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Min, Max
from django.contrib import messages
from .models import Product, Category, Review, ProductInventory


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


def category_detail(request, category_slug):  # یا category_slug بسته به تعریف URL شما
    category = get_object_or_404(Category, slug=category_slug, is_active=True)

    # دریافت زیردسته‌های این دسته‌بندی
    subcategories = Category.objects.filter(parent=category, is_active=True)

    # دریافت محصولات این دسته‌بندی و زیردسته‌های آن
    products = Product.objects.filter(is_active=True)

    if subcategories.exists():
        # اگر زیردسته دارد، محصولات خود دسته و زیردسته‌ها را نمایش بده
        category_ids = [category.id] + list(subcategories.values_list('id', flat=True))
        products = products.filter(category_id__in=category_ids)
    else:
        # اگر زیردسته ندارد، فقط محصولات خود دسته را نمایش بده
        products = products.filter(category=category)

    # دریافت تمام برندهای موجود در محصولات این دسته
    all_brands = Product.objects.filter(
        category__in=[category] + list(subcategories),
        is_active=True
    ).values_list('brand', flat=True).distinct()

    # دریافت تمام سایزهای موجود در محصولات این دسته
    all_sizes = set()
    for product in Product.objects.filter(
            category__in=[category] + list(subcategories),
            is_active=True
    ):
        if hasattr(product, 'sizes') and product.sizes:
            all_sizes.update(product.sizes)
    all_sizes = sorted(list(all_sizes))

    # دریافت تمام رنگ‌های موجود در محصولات این دسته
    all_colors = set()
    all_color_codes = {}
    for product in Product.objects.filter(
            category__in=[category] + list(subcategories),
            is_active=True
    ):
        if hasattr(product, 'colors') and product.colors:
            for i, color in enumerate(product.colors):
                all_colors.add(color)
                if hasattr(product, 'color_codes') and product.color_codes and i < len(product.color_codes):
                    all_color_codes[color] = product.color_codes[i]
    all_colors = sorted(list(all_colors))

    # دریافت محدوده قیمت محصولات
    price_range = products.aggregate(min_price=Min('price'), max_price=Max('price'))

    # دریافت پارامترهای فیلتر از URL
    filters_applied = False
    filter_params = {}

    # فیلتر بر اساس برند
    brand = request.GET.get('brand')
    if brand and brand != 'none':
        filter_params['brand'] = brand
        filters_applied = True

    # فیلتر بر اساس قیمت
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if min_price and min_price.strip():
        try:
            min_price = int(min_price)
            filter_params['min_price'] = min_price
            filters_applied = True
        except (ValueError, TypeError):
            min_price = None

    if max_price and max_price.strip():
        try:
            max_price = int(max_price)
            filter_params['max_price'] = max_price
            filters_applied = True
        except (ValueError, TypeError):
            max_price = None

    # فیلتر بر اساس سایز
    size = request.GET.get('size')
    if size and size != 'none':
        filter_params['size'] = size
        filters_applied = True

    # فیلتر بر اساس رنگ
    color = request.GET.get('color')
    if color and color != 'none':
        filter_params['color'] = color
        filters_applied = True

    # اعمال فیلترها - روش جدید
    # ابتدا محصولات را بر اساس فیلترهای پایگاه داده فیلتر می‌کنیم
    if 'brand' in filter_params:
        products = products.filter(brand=filter_params['brand'])

    if 'min_price' in filter_params:
        products = products.filter(price__gte=filter_params['min_price'])

    if 'max_price' in filter_params:
        products = products.filter(price__lte=filter_params['max_price'])

    # حالا محصولات را به لیست تبدیل می‌کنیم تا بتوانیم فیلترهای پیچیده‌تر را اعمال کنیم
    filtered_products = list(products)
    final_products = []

    # اعمال فیلترهای سایز و رنگ
    for product in filtered_products:
        # بررسی فیلتر سایز
        if 'size' in filter_params:
            if not hasattr(product, 'sizes') or not product.sizes or filter_params['size'] not in product.sizes:
                continue

        # بررسی فیلتر رنگ
        if 'color' in filter_params:
            if not hasattr(product, 'colors') or not product.colors or filter_params['color'] not in product.colors:
                continue

        # اگر محصول از همه فیلترها عبور کرد، آن را به لیست نهایی اضافه می‌کنیم
        final_products.append(product)

    # مرتب‌سازی محصولات
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_low':
        final_products = sorted(final_products, key=lambda p: p.price)
    elif sort_by == 'price_high':
        final_products = sorted(final_products, key=lambda p: -p.price)
    elif sort_by == 'popular':
        final_products = sorted(final_products, key=lambda p: -p.total_sales if hasattr(p, 'total_sales') else 0)
    else:  # newest
        final_products = sorted(final_products, key=lambda p: p.created_at, reverse=True)

    # محدود کردن تعداد محصولات به 6 تا
    if sort_by in ['price_low', 'price_high', 'popular', 'newest']:
        final_products = final_products[:6]

    context = {
        'category': category,
        'subcategories': subcategories,
        'products': final_products,
        'all_brands': all_brands,
        'all_sizes': all_sizes,
        'all_colors': all_colors,
        'all_color_codes': all_color_codes,
        'price_range': price_range,
        'current_filters': {
            'brand': brand if brand and brand != 'none' else None,
            'size': size if size and size != 'none' else None,
            'color': color if color and color != 'none' else None,
            'min_price': min_price,
            'max_price': max_price,
            'sort': sort_by
        },
        'filters_applied': filters_applied,
        'filter_params': filter_params
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