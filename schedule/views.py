import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from .models import ScheduledSurvey


class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'schedule/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        scheduled = (
            ScheduledSurvey.objects
            .select_related('contract', 'contract__client', 'contract__client__branch')
            .order_by('scheduled_date')
        )

        color_map = {
            ScheduledSurvey.Status.PENDING: '#28a745',
            ScheduledSurvey.Status.COMPLETED: '#007bff',
            ScheduledSurvey.Status.OVERDUE: '#dc3545',
        }

        events = []
        upcoming = []
        for s in scheduled:
            status = s.status
            if s.is_overdue:
                status = ScheduledSurvey.Status.OVERDUE

            events.append({
                'id': s.pk,
                'title': s.contract.client.name,
                'start': s.scheduled_date.isoformat(),
                'color': color_map.get(status, '#6c757d'),
                'extendedProps': {
                    'client_id': s.contract.client.pk,
                    'contract_id': s.contract.pk,
                    'branch': str(s.contract.client.branch),
                    'status': s.get_status_display(),
                },
            })

            if s.status == ScheduledSurvey.Status.PENDING:
                upcoming.append(s)

        context['events_json'] = json.dumps(events)
        context['upcoming'] = upcoming[:20]

        first_pending = next(
            (s for s in scheduled if s.status == ScheduledSurvey.Status.PENDING),
            None,
        )
        context['initial_date'] = first_pending.scheduled_date.isoformat() if first_pending else ''
        return context


class CalendarEventsApiView(LoginRequiredMixin, View):
    """API JSON para o FullCalendar."""
    def get(self, request):
        start = request.GET.get('start')
        end = request.GET.get('end')

        qs = ScheduledSurvey.objects.select_related(
            'contract', 'contract__client', 'contract__client__branch'
        )

        if start:
            qs = qs.filter(scheduled_date__gte=start)
        if end:
            qs = qs.filter(scheduled_date__lte=end)

        color_map = {
            ScheduledSurvey.Status.PENDING: '#28a745',
            ScheduledSurvey.Status.COMPLETED: '#007bff',
            ScheduledSurvey.Status.OVERDUE: '#dc3545',
        }

        events = []
        for scheduled in qs:
            status = scheduled.status
            if scheduled.is_overdue:
                status = ScheduledSurvey.Status.OVERDUE

            events.append({
                'id': scheduled.pk,
                'title': scheduled.contract.client.name,
                'start': scheduled.scheduled_date.isoformat(),
                'color': color_map.get(status, '#6c757d'),
                'extendedProps': {
                    'client_id': scheduled.contract.client.pk,
                    'contract_id': scheduled.contract.pk,
                    'branch': str(scheduled.contract.client.branch),
                    'status': scheduled.get_status_display(),
                },
            })

        return JsonResponse(events, safe=False)
