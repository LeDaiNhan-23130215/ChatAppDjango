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
            'motivation_level'
        ]
