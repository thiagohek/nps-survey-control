from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import CreateView, ListView

from clients.models import Client
from .forms import SurveyForm, ServiceScoreForm
from .models import Survey, ServiceScore


class SurveyCreateView(LoginRequiredMixin, CreateView):
    model = Survey
    form_class = SurveyForm
    template_name = 'surveys/survey_form.html'

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
                client = Client.objects.get(pk=client_id)
                context['selected_client'] = client
                context['client_services'] = client.active_services
            except Client.DoesNotExist:
                pass
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        survey = form.save()

        # Salvar notas por serviço
        client = survey.client
        for service in client.active_services:
            score_value = self.request.POST.get(f'score_{service.id}')
            if score_value:
                ServiceScore.objects.create(
                    survey=survey,
                    service=service,
                    score=int(score_value),
                )

        # Agendar próxima pesquisa se não for histórica
        if not survey.is_historical:
            self._schedule_next_survey(survey)

        return redirect('clients:detail', pk=client.pk)

    def _schedule_next_survey(self, survey):
        from schedule.models import ScheduledSurvey
        client = survey.client
        next_date = survey.date_conducted + timedelta(days=client.survey_frequency_days)

        ScheduledSurvey.objects.update_or_create(
            client=client,
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
        qs = super().get_queryset().select_related('client', 'client__branch', 'created_by')
        client_id = self.request.GET.get('client')
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs


class DashboardView(LoginRequiredMixin, View):
    """Redireciona para a página unificada do cliente."""
    def get(self, request, client_id):
        return redirect('clients:detail', pk=client_id)


class ClientServicesApiView(LoginRequiredMixin, View):
    """API para carregar serviços de um cliente (usado no formulário)."""
    def get(self, request, client_id):
        client = get_object_or_404(Client, pk=client_id)
        services = list(client.active_services.values('id', 'name'))
        return JsonResponse({'services': services})


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
