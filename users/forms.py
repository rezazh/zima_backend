from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from .models import CustomUser


class SignUpForm(UserCreationForm):
    """فرم ثبت‌نام کاربر"""
    phone_number = forms.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r'^09\d{9}$',
                message='شماره موبایل باید با 09 شروع شده و 11 رقم باشد.'
            )
        ],
        required=True,
        help_text='مثال: 09123456789'
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'password1', 'password2')


class LoginForm(forms.Form):
    """فرم ورود کاربر"""
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    remember = forms.BooleanField(required=False)


class UserProfileForm(forms.ModelForm):
    """فرم ویرایش پروفایل کاربر"""

    class Meta:
        model = CustomUser
        fields = ('email', 'phone_number')