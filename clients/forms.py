from django import forms
from organizations.models import Service
from .models import Client, ClientService


class ClientForm(forms.ModelForm):
    active_services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label='Serviços Contratados',
    )

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se editando, marcar os serviços ativos do cliente
        if self.instance.pk:
            self.fields['active_services'].initial = (
                self.instance.services
                .filter(clientservice__is_active=True)
                .values_list('pk', flat=True)
            )

    def save(self, commit=True):
        client = super().save(commit=commit)
        if commit:
            self._save_services(client)
        return client

    def _save_services(self, client):
        selected_services = set(self.cleaned_data['active_services'].values_list('pk', flat=True))

        # Serviços já associados ao cliente
        existing = {
            cs.service_id: cs
            for cs in ClientService.objects.filter(client=client)
        }

        for service_id, cs in existing.items():
            if service_id in selected_services:
                # Serviço selecionado: reativar se estava cancelado
                if not cs.is_active:
                    cs.is_active = True
                    cs.end_date = None
                    cs.save()
                selected_services.discard(service_id)
            else:
                # Serviço desmarcado: cancelar se estava ativo
                if cs.is_active:
                    from django.utils import timezone
                    cs.is_active = False
                    cs.end_date = timezone.now().date()
                    cs.save()

        # Serviços novos (não existiam antes)
        for service_id in selected_services:
            ClientService.objects.create(
                client=client,
                service_id=service_id,
            )
