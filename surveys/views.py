from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import CreateView, ListView

from contracts.models import Contract, ContractService
from .forms import SurveyForm
from .models import Survey, ServiceScore


class SurveyCreateView(LoginRequiredMixin, CreateView):
    model = Survey
    form_class = SurveyForm
    template_name = 'surveys/survey_form.html'

    def get_initial(self):
        initial = super().get_initial()
        contract_id = self.request.GET.get('contract')
        if contract_id:
            initial['contract'] = contract_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract_id = self.request.GET.get('contract') or self.request.POST.get('contract')
        if contract_id:
            try:
                contract = Contract.objects.select_related('client').get(pk=contract_id)
                context['selected_contract'] = contract
                context['contract_services'] = list(
                    ContractService.objects.filter(contract=contract)
                    .select_related('service')
                )
            except Contract.DoesNotExist:
                pass
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        survey = form.save()

        # Salvar notas por serviço (do contrato, não do cliente)
        contract = survey.contract
        contract_services = ContractService.objects.filter(
            contract=contract
        ).select_related('service')

        for cs in contract_services:
            score_value = self.request.POST.get(f'score_{cs.service_id}')
            if score_value:
                ServiceScore.objects.create(
                    survey=survey,
                    service=cs.service,
                    score=int(score_value),
                )

        # Atualizar last_survey_date do contrato
        contract.last_survey_date = survey.date_conducted
        contract.save(update_fields=['last_survey_date'])

        # Agendar próxima pesquisa se não for histórica
        if not survey.is_historical:
            self._schedule_next_survey(survey)

        return redirect('contracts:detail', pk=contract.pk)

    def _schedule_next_survey(self, survey):
        from schedule.models import ScheduledSurvey
        contract = survey.contract
        next_date = survey.date_conducted + timedelta(days=contract.survey_frequency_days)

        ScheduledSurvey.objects.update_or_create(
            contract=contract,
            defaults={
                'scheduled_date': next_date,
                'status': ScheduledSurvey.Status.PENDING,
                'last_survey': survey,
            },
        )


class SurveyListView(LoginRequiredMixin, ListView):
    model = Survey
    template_name = 'surveys/survey_list.html'
    context_object_name = 'surveys'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            'contract', 'contract__client', 'contract__client__branch', 'created_by'
        )
        contract_id = self.request.GET.get('contract')
        if contract_id:
            qs = qs.filter(contract_id=contract_id)
        client_id = self.request.GET.get('client')
        if client_id:
            qs = qs.filter(contract__client_id=client_id)
        return qs


class DashboardView(LoginRequiredMixin, View):
    """Redireciona para a página do contrato ou do cliente."""
    def get(self, request, client_id):
        return redirect('clients:detail', pk=client_id)


class ContractServicesApiView(LoginRequiredMixin, View):
    """API para carregar serviços de um contrato (usado no formulário)."""
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


class SurveyDetailApiView(LoginRequiredMixin, View):
    """API JSON com resumo completo de uma pesquisa (usado no modal)."""
    def get(self, request, survey_id):
        survey = get_object_or_404(
            Survey.objects.prefetch_related(
                'service_scores__service', 'strengths', 'improvements'
            ),
            pk=survey_id,
        )
        data = {
            'date': survey.date_conducted.strftime('%d/%m/%Y'),
            'respondent_name': survey.respondent_name,
            'respondent_role': survey.respondent_role,
            'nps_score': survey.nps_score,
            'comments': survey.comments,
            'is_historical': survey.is_historical,
            'service_scores': [
                {'service': ss.service.name, 'score': ss.score}
                for ss in survey.service_scores.all()
            ],
            'strengths': [s.name for s in survey.strengths.all()],
            'improvements': [i.name for i in survey.improvements.all()],
        }
        return JsonResponse(data)
