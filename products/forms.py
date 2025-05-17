from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    """فرم ثبت نظر برای محصول"""
    class Meta:
        model = Review
        fields = ('rating', 'comment')
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }