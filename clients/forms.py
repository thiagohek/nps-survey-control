from django import forms
from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            'name', 'cnpj', 'contact_name', 'contact_phone',
            'contact_email', 'size', 'branch',
        ]
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'size': forms.Select(attrs={'class': 'form-select'}),
        }
