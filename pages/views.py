from django.shortcuts import render
from django.shortcuts import render
from .models import Slider
from products.models import Product, Banner, Category


def home(request):
    sliders = Slider.objects.filter(is_active=True).order_by('order')

    main_categories = {
        'mens': Category.objects.filter(slug='mens-clothing').first(),
        'womens': Category.objects.filter(slug='womens-clothing').first(),
        'boys': Category.objects.filter(slug='boys-clothing').first(),
        'girls': Category.objects.filter(slug='girls-clothing').first(),
    }
    featured_products = Product.objects.filter(is_active=True, is_featured=True).order_by('-created_at')[:8]

    new_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]

    top_banners = Banner.objects.filter(is_active=True, position='home_top').order_by('order')
    middle_banners = Banner.objects.filter(is_active=True, position='home_middle').order_by('order')
    bottom_banners = Banner.objects.filter(is_active=True, position='home_bottom').order_by('order')
    sidebar_banners = Banner.objects.filter(is_active=True, position='sidebar').order_by('order')  # اضافه شد

    context = {
        'sliders': sliders,
        'featured_products': featured_products,
        'new_products': new_products,
        'top_banners': top_banners,
        'middle_banners': middle_banners,
        'bottom_banners': bottom_banners,
        'sidebar_banners': sidebar_banners,  # اضافه شد
        'main_categories': main_categories,
    }
    return render(request, 'pages/home.html', context)


def about(request):
    """صفحه درباره ما"""
    return render(request, 'pages/about.html')


def contact(request):
    """صفحه تماس با ما"""
    return render(request, 'pages/contact.html')


def faq(request):
    """صفحه سوالات متداول"""
    return render(request, 'pages/faq.html')


def privacy(request):
    """صفحه حریم خصوصی"""
    return render(request, 'pages/privacy.html')


def terms(request):
    """صفحه قوانین و مقررات"""
    return render(request, 'pages/terms.html')


def shipping(request):
    """صفحه شیوه‌های ارسال"""
    return render(request, 'pages/shipping.html')


def returns(request):
    """صفحه شرایط بازگشت کالا"""
    return render(request, 'pages/returns.html')


def newsletter(request):
    """عضویت در خبرنامه"""
    if request.method == 'POST':
        email = request.POST.get('email')
        from django.contrib import messages
        messages.success(request, 'ایمیل شما با موفقیت در خبرنامه ثبت شد.')

    from django.shortcuts import redirect
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def size_guide_view(request):
    """
    Renders the Zima size guide page.
    """
    return render(request, 'pages/size_guide.html')