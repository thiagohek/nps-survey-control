from django import forms

from organizations.models import Service
from .models import Contract, ContractService


class ContractForm(forms.ModelForm):
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label='Servicos Prestados',
    )

    class Meta:
        model = Contract
        fields = ['client', 'start_date']
        widgets = {
            'client': forms.HiddenInput(),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def clean_client(self):
        client = self.cleaned_data['client']
        if Contract.objects.filter(client=client, status=Contract.Status.ACTIVE).exists():
            raise forms.ValidationError(
                'Este cliente ja possui um contrato ativo. Encerre-o antes de criar um novo.'
            )
        return client

    def save(self, commit=True):
        contract = super().save(commit=False)
        client = contract.client

        # Snapshot do estado do cliente
        contract.company_size = client.size
        from .services import get_frequency
        contract.survey_frequency_days = get_frequency(client.size)
        contract.status = Contract.Status.ACTIVE

        if commit:
            contract.save()
            # Criar ContractService para cada servico selecionado
            for service in self.cleaned_data['services']:
                ContractService.objects.create(
                    contract=contract,
                    service=service,
                )
        return contract
