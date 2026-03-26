from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from accounts.mixins import ResearcherOrDirectorMixin
from contracts.models import ContractService
from .forms import ClientForm
from .models import Client


class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('branch').prefetch_related(
            'services', 'contracts'
        )
        user = self.request.user

        # Gerente so ve clientes das suas filiais
        if user.is_manager():
            qs = qs.filter(branch__in=user.branch.all())

        # Filtros opcionais
        branch = self.request.GET.get('branch')
        if branch:
            qs = qs.filter(branch_id=branch)

        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(name__icontains=search)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from organizations.models import Filial
        user = self.request.user
        if user.is_manager():
            context['branches'] = user.branch.all()
        else:
            context['branches'] = Filial.objects.filter(is_active=True)
        return context


class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Servicos do contrato ativo
        active_contract = self.object.active_contract
        if active_contract:
            context['contract_services'] = ContractService.objects.filter(
                contract=active_contract
            ).select_related('service').order_by('service__name')
        else:
            context['contract_services'] = []

        # Contratos do cliente com resumo
        contracts = (
            self.object.contracts
            .prefetch_related('surveys')
            .order_by('-start_date')
        )

        contracts_data = []
        for contract in contracts:
            surveys = contract.surveys.all()
            survey_count = surveys.count()
            avg_nps = surveys.aggregate(avg=Avg('nps_score'))['avg']
            contracts_data.append({
                'contract': contract,
                'survey_count': survey_count,
                'avg_nps': round(avg_nps, 1) if avg_nps else None,
            })

        context['contracts_data'] = contracts_data
        context['has_active_contract'] = self.object.has_active_contract

        return context


class ClientCreateView(ResearcherOrDirectorMixin, LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_url = reverse_lazy('clients:list')


class ClientUpdateView(ResearcherOrDirectorMixin, LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_url = reverse_lazy('clients:list')
