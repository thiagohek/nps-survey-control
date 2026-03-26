import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from accounts.mixins import ResearcherOrDirectorMixin
from schedule.models import ScheduledSurvey
from .forms import ClientForm
from .models import Client, ClientService


class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('branch').prefetch_related('services')
        user = self.request.user

        # Gerente só vê clientes das suas filiais
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

        # Serviços
        context['client_services'] = ClientService.objects.filter(
            client=self.object
        ).select_related('service').order_by('-is_active', 'service__name')

        # Próxima pesquisa agendada
        try:
            context['next_survey'] = ScheduledSurvey.objects.get(client=self.object)
        except ScheduledSurvey.DoesNotExist:
            context['next_survey'] = None

        # Todas as pesquisas (ordenadas cronologicamente para gráficos)
        surveys = list(
            self.object.surveys
            .order_by('date_conducted')
            .prefetch_related('service_scores__service', 'strengths', 'improvements')
        )
        context['surveys'] = surveys

        # Dados JSON para Chart.js (inline, sem AJAX)
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
