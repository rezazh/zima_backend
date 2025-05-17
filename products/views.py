from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.contrib import messages
from .models import Product, Category, Review


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
    if sort == 'priceیلتر':
        filter_options = {
            'sizes': ['S', 'M', 'L', 'XL', 'XXL'],
            'colors': ['سفید', 'مشکی', 'آبی', 'قرمز', 'سبز'],
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
    """نمایش جزئیات محصول"""
    product = get_object_or_404(Product, id=product_id)

    # محصولات مشابه
    similar_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'similar_products': similar_products,
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