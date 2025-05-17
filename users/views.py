from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignUpForm, LoginForm, UserProfileForm
from .models import Address


def signup(request):
    """ثبت‌نام کاربر جدید"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'ثبت‌نام با موفقیت انجام شد.')
            return redirect('home')
    else:
        form = SignUpForm()

    return render(request, 'users/signup.html', {'form': form})


def login_view(request):
    """ورود کاربر"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.POST.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {
        'form': form,
        'next': request.GET.get('next', '')
    })


@login_required
def logout_view(request):
    """خروج کاربر"""
    logout(request)
    messages.success(request, 'با موفقیت خارج شدید.')
    return redirect('home')


@login_required
def profile(request):
    """نمایش و ویرایش پروفایل کاربر"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'اطلاعات حساب کاربری با موفقیت به‌روزرسانی شد.')
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'users/profile.html', {'form': form})


@login_required
def change_password(request):
    """تغییر رمز عبور"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # بررسی صحت رمز فعلی
        if not request.user.check_password(current_password):
            messages.error(request, 'رمز عبور فعلی اشتباه است.')
            return redirect('users:change_password')

        # بررسی یکسان بودن رمز جدید و تکرار آن
        if new_password != confirm_password:
            messages.error(request, 'رمز عبور جدید و تکرار آن یکسان نیستند.')
            return redirect('users:change_password')

        # تغییر رمز عبور
        request.user.set_password(new_password)
        request.user.save()

        # ورود مجدد با رمز جدید
        user = authenticate(username=request.user.username, password=new_password)
        login(request, user)

        messages.success(request, 'رمز عبور با موفقیت تغییر یافت.')
        return redirect('users:profile')

    return render(request, 'users/change_password.html')


@login_required
def addresses(request):
    """مدیریت آدرس‌های کاربر"""
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'users/addresses.html', {'addresses': addresses})


@login_required
def add_address(request):
    """افزودن آدرس جدید"""
    if request.method == 'POST':
        full_address = request.POST.get('full_address')
        postal_code = request.POST.get('postal_code')

        Address.objects.create(
            user=request.user,
            full_address=full_address,
            postal_code=postal_code
        )

        messages.success(request, 'آدرس جدید با موفقیت اضافه شد.')

    return redirect('users:addresses')


@login_required
def edit_address(request, address_id):
    """ویرایش آدرس"""
    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == 'POST':
        full_address = request.POST.get('full_address')
        postal_code = request.POST.get('postal_code')

        address.full_address = full_address
        address.postal_code = postal_code
        address.save()

        messages.success(request, 'آدرس با موفقیت ویرایش شد.')

    return redirect('users:addresses')


@login_required
def delete_address(request, address_id):
    """حذف آدرس"""
    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == 'POST':
        address.delete()
        messages.success(request, 'آدرس با موفقیت حذف شد.')

    return redirect('users:addresses')