from django import forms

class AddToCartForm(forms.Form):
    """فرم افزودن محصول به سبد خرید"""
    size = forms.CharField(required=True)
    color = forms.CharField(required=True)
    quantity = forms.IntegerField(min_value=1, initial=1)

class CouponForm(forms.Form):
    """فرم اعمال کد تخفیف"""
    code = forms.CharField(max_length=50, required=True)