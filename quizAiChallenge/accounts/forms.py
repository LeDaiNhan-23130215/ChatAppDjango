from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class CompleteProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'declared_level',
            'goals',
            'education',
            'profession',
            'referred_frequency',
            'motivation_level',
            'hobby'
        ]
        widgets = {
            'declared_level': forms.Select(attrs={'class': 'form-control'}),
            'goals': forms.Select(attrs={'class': 'form-control'}),
            'education': forms.Select(attrs={'class': 'form-control'}),
            'profession': forms.Select(attrs={'class': 'form-control'}),
            'referred_frequency': forms.Select(attrs={'class': 'form-control'}),
            'motivation_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'hobby': forms.Select(attrs={'class': 'form-control'}),
        }
