import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView

from accounts.mixins import ResearcherOrDirectorMixin
from clients.models import Client
from .forms import ContractForm
from .models import Contract, ContractService
from .services import close_contract


class ContractCreateView(ResearcherOrDirectorMixin, LoginRequiredMixin, CreateView):
    model = Contract
    form_class = ContractForm
    template_name = 'contracts/contract_form.html'

    def get_initial(self):
        initial = super().get_initial()
        client_id = self.request.GET.get('client')
        if client_id:
            initial['client'] = client_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client_id = self.request.GET.get('client') or self.request.POST.get('client')
        if client_id:
            try:
                context['client'] = Client.objects.get(pk=client_id)
            except Client.DoesNotExist:
                pass
        return context

    def get_success_url(self):
        return reverse('contracts:detail', kwargs={'pk': self.object.pk})


class ContractDetailView(LoginRequiredMixin, DetailView):
    model = Contract
    template_name = 'contracts/contract_detail.html'
    context_object_name = 'contract'

    def get_queryset(self):
        return super().get_queryset().select_related('client', 'client__branch')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract = self.object

        # Serviços do contrato (snapshot)
        context['contract_services'] = ContractService.objects.filter(
            contract=contract
        ).select_related('service').order_by('service__name')

        # Próxima pesquisa agendada
        from schedule.models import ScheduledSurvey
        try:
            context['next_survey'] = ScheduledSurvey.objects.get(contract=contract)
        except ScheduledSurvey.DoesNotExist:
            context['next_survey'] = None

        # Todas as pesquisas do contrato
        surveys = list(
            contract.surveys
            .order_by('date_conducted')
            .prefetch_related('service_scores__service', 'strengths', 'improvements')
        )
        context['surveys'] = surveys

        # Dados JSON para Chart.js
        if surveys:
            chart_data = {
                'labels': [s.date_conducted.strftime('%d/%m/%Y') for s in surveys],
                'nps_scores': [s.nps_score for s in surveys],
                'services': {},
            }
            for survey in surveys:
                for ss in survey.service_scores.all():
                    name = ss.service.name
                    if name not in chart_data['services']:
                        chart_data['services'][name] = []
                    chart_data['services'][name].append(ss.score)
            context['chart_data_json'] = json.dumps(chart_data)

        return context


class ContractCloseView(ResearcherOrDirectorMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        contract = get_object_or_404(Contract, pk=pk)
        try:
            close_contract(contract)
            messages.success(request, f'Contrato de "{contract.client.name}" encerrado com sucesso.')
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('clients:detail', pk=contract.client.pk)


class ContractServicesApiView(LoginRequiredMixin, View):
    """API para carregar serviços de um contrato (usado no formulário de pesquisa)."""
    def get(self, request, contract_id):
        contract = get_object_or_404(Contract, pk=contract_id)
        services = list(
            ContractService.objects.filter(contract=contract)
            .select_related('service')
            .values('service__id', 'service__name')
        )
        return JsonResponse({
            'services': [
                {'id': s['service__id'], 'name': s['service__name']}
                for s in services
            ]
        })
