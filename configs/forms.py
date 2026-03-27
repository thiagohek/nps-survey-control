from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from organizations.models import Filial, Service
from surveys.models import Strength, Improvement

User = get_user_model()


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    password_confirm = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'branch']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'branch': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['branch'].queryset = Filial.objects.filter(is_active=True)
        self.fields['branch'].required = False
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = User.objects.filter(username=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Já existe um usuário com este email.')
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'As senhas não coincidem.')
        role = cleaned_data.get('role')
        if role != User.Role.MANAGER:
            cleaned_data['branch'] = Filial.objects.none()
        elif not cleaned_data.get('branch'):
            self.add_error('branch', 'Selecione ao menos uma filial para o gerente.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            self.save_m2m()
        return user


class UserUpdateForm(forms.ModelForm):
    password = forms.CharField(
        label='Nova senha',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Deixe em branco para não alterar.',
    )
    password_confirm = forms.CharField(
        label='Confirmar nova senha',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'branch']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'branch': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['branch'].queryset = Filial.objects.filter(is_active=True)
        self.fields['branch'].required = False
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = User.objects.filter(username=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Já existe um usuário com este email.')
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'As senhas não coincidem.')
        role = cleaned_data.get('role')
        if role != User.Role.MANAGER:
            cleaned_data['branch'] = Filial.objects.none()
        elif not cleaned_data.get('branch'):
            self.add_error('branch', 'Selecione ao menos uma filial para o gerente.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
            self.save_m2m()
        return user


class StrengthForm(forms.ModelForm):
    class Meta:
        model = Strength
        fields = ['name', 'is_active']


class ImprovementForm(forms.ModelForm):
    class Meta:
        model = Improvement
        fields = ['name', 'is_active']


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'is_active']


class FilialForm(forms.ModelForm):
    class Meta:
        model = Filial
        fields = ['name', 'code', 'address', 'is_active']
