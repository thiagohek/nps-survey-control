import json
from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Avg, Q, Prefetch
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.views import View

from contracts.models import Contract, ContractService
from organizations.models import Filial
from surveys.models import Survey, ServiceScore, Strength, Improvement


def _calc_nps(total, promotores, detratores):
    """Fórmula NPS padrão: ((Promotores - Detratores) / Total) × 100."""
    if not total:
        return None
    return round(((promotores - detratores) / total) * 100)


def _nps_zone(score):
    """Retorna (label, badge_class Bootstrap) para o score NPS."""
    if score is None:
        return 'Sem dados', 'secondary'
    if score >= 75:
        return 'Excelência', 'success'
    if score >= 50:
        return 'Qualidade', 'info'
    if score >= 0:
        return 'Aperfeiçoamento', 'warning'
    return 'Crítico', 'danger'


def _nps_chart_color(score):
    """Cor hex para barras dos gráficos Chart.js."""
    if score is None:
        return '#9e9e9e'
    if score >= 50:
        return '#2e7d32'
    if score >= 0:
        return '#f57f17'
    return '#c62828'


class CEODashboardView(LoginRequiredMixin, View):
    template_name = 'dashboard/ceo_dashboard.html'

    def get(self, request):
        today = date.today()

        # --- Período ---
        preset = request.GET.get('preset', '12')
        date_from_str = request.GET.get('date_from', '')
        date_to_str = request.GET.get('date_to', '')

        if date_from_str and date_to_str:
            try:
                date_from = date.fromisoformat(date_from_str)
                date_to = date.fromisoformat(date_to_str)
                preset = ''
            except ValueError:
                date_from = today - timedelta(days=365)
                date_to = today
                preset = '12'
        else:
            days = {'1': 30, '3': 90, '6': 180, '12': 365}.get(preset, 365)
            date_from = today - timedelta(days=days)
            date_to = today

        filial_id = request.GET.get('filial', '')
        porte = request.GET.get('porte', '')
        user = request.user

        # --- Base queryset (período + filial + porte) ---
        surveys = Survey.objects.filter(
            date_conducted__gte=date_from,
            date_conducted__lte=date_to,
        )
        if user.is_manager():
            surveys = surveys.filter(contract__client__branch__in=user.branch.all())
        if filial_id:
            surveys = surveys.filter(contract__client__branch_id=filial_id)
        if porte:
            surveys = surveys.filter(contract__client__size=porte)

        # --- KPIs ---
        total = surveys.count()
        promotores_count = surveys.filter(nps_score__gte=9).count()
        detratores_count = surveys.filter(nps_score__lte=6).count()
        neutros_count = total - promotores_count - detratores_count
        nps_geral = _calc_nps(total, promotores_count, detratores_count)
        pct_p = round(promotores_count / total * 100) if total else 0
        pct_n = round(neutros_count / total * 100) if total else 0
        pct_d = round(detratores_count / total * 100) if total else 0
        empresas_avaliadas = surveys.values('contract__client').distinct().count()
        nps_geral_label, nps_geral_badge = _nps_zone(nps_geral)

        # --- Evolução mensal ---
        monthly_qs = (
            surveys
            .annotate(mes=TruncMonth('date_conducted'))
            .values('mes')
            .annotate(
                total=Count('id'),
                promotores=Count('id', filter=Q(nps_score__gte=9)),
                detratores=Count('id', filter=Q(nps_score__lte=6)),
            )
            .order_by('mes')
        )
        monthly_labels = []
        monthly_nps = []
        for m in monthly_qs:
            monthly_labels.append(m['mes'].strftime('%b/%y'))
            monthly_nps.append(_calc_nps(m['total'], m['promotores'], m['detratores']))

        # --- NPS por Filial ---
        filial_qs = (
            surveys
            .values('contract__client__branch__name')
            .annotate(
                total=Count('id'),
                promotores=Count('id', filter=Q(nps_score__gte=9)),
                detratores=Count('id', filter=Q(nps_score__lte=6)),
            )
            .order_by('contract__client__branch__name')
        )
        filial_chart = []
        for f in filial_qs:
            nps = _calc_nps(f['total'], f['promotores'], f['detratores'])
            filial_chart.append({
                'name': f['contract__client__branch__name'] or '—',
                'nps': nps,
                'total': f['total'],
            })
        filial_chart_sorted = sorted(
            filial_chart,
            key=lambda x: (x['nps'] is None, -(x['nps'] if x['nps'] is not None else -999)),
        )

        # --- NPS por Porte ---
        PORTE_LABEL = {'S': 'Pequeno', 'M': 'Médio', 'L': 'Grande'}
        PORTE_ORDER = {'Pequeno': 0, 'Médio': 1, 'Grande': 2}
        porte_qs = (
            surveys
            .values('contract__client__size')
            .annotate(
                total=Count('id'),
                promotores=Count('id', filter=Q(nps_score__gte=9)),
                detratores=Count('id', filter=Q(nps_score__lte=6)),
            )
        )
        porte_chart = []
        for p in porte_qs:
            nps = _calc_nps(p['total'], p['promotores'], p['detratores'])
            label = PORTE_LABEL.get(p['contract__client__size'], p['contract__client__size'])
            porte_chart.append({'name': label, 'nps': nps})
        porte_chart.sort(key=lambda x: PORTE_ORDER.get(x['name'], 99))

        # --- NPS por Serviço ---
        service_qs = (
            ServiceScore.objects
            .filter(survey__in=surveys)
            .values('service__name')
            .annotate(
                total=Count('id'),
                promotores=Count('id', filter=Q(score__gte=9)),
                detratores=Count('id', filter=Q(score__lte=6)),
            )
            .order_by('service__name')
        )
        service_chart = []
        for s in service_qs:
            nps = _calc_nps(s['total'], s['promotores'], s['detratores'])
            service_chart.append({'name': s['service__name'], 'nps': nps})
        service_chart_sorted = sorted(
            service_chart,
            key=lambda x: (x['nps'] is None, -(x['nps'] if x['nps'] is not None else -999)),
        )

        # --- Ranking de empresas (critério: média raw score 0-10) ---
        # Apenas contratos ativos para não exibir empresas encerradas no Top 5
        surveys_active = surveys.filter(contract__status=Contract.Status.ACTIVE)
        client_qs = (
            surveys_active
            .values('contract__client__id', 'contract__client__name', 'contract__client__branch__name')
            .annotate(
                total=Count('id'),
                avg_score=Avg('nps_score'),
                promotores=Count('id', filter=Q(nps_score__gte=9)),
                detratores=Count('id', filter=Q(nps_score__lte=6)),
            )
        )
        client_list = []
        for c in client_qs:
            nps = _calc_nps(c['total'], c['promotores'], c['detratores'])
            avg = round(c['avg_score'], 1) if c['avg_score'] is not None else None
            label, badge = _nps_zone(nps)
            client_list.append({
                'name': c['contract__client__name'],
                'branch': c['contract__client__branch__name'] or '—',
                'avg_score': avg,
                'nps': nps,
                'nps_label': label,
                'nps_badge': badge,
                'total': c['total'],
            })
        best_clients = sorted(
            [c for c in client_list if c['avg_score'] is not None and c['avg_score'] >= 7.0],
            key=lambda x: -(x['avg_score'] or 0),
        )[:5]
        worst_clients = sorted(
            [c for c in client_list if c['avg_score'] is not None and c['avg_score'] < 7.0],
            key=lambda x: (x['avg_score'] or 0),
        )[:5]

        # --- Ranking de filiais ---
        filial_ranking = []
        for f in filial_chart_sorted:
            label, badge = _nps_zone(f['nps'])
            filial_ranking.append({**f, 'nps_label': label, 'nps_badge': badge})

        # --- Atenção Urgente: últimas 2 pesquisas consecutivas com score < 7 ---
        # Filtro de filial aplicado; período e porte NÃO filtram (mostra contratos ativos)
        urgent_qs = (
            Contract.objects
            .filter(status=Contract.Status.ACTIVE)
            .prefetch_related(
                Prefetch('surveys', queryset=Survey.objects.order_by('-date_conducted')),
                Prefetch('contract_services', queryset=ContractService.objects.select_related('service')),
            )
            .select_related('client__branch')
        )
        if user.is_manager():
            urgent_qs = urgent_qs.filter(client__branch__in=user.branch.all())
        if filial_id:
            urgent_qs = urgent_qs.filter(client__branch_id=filial_id)

        urgent_list = []
        for contract in urgent_qs:
            recent = list(contract.surveys.all()[:2])
            if len(recent) >= 2 and recent[0].nps_score < 7 and recent[1].nps_score < 7:
                services_at_risk = []
                for cs in contract.contract_services.all():
                    s_scores = list(
                        ServiceScore.objects
                        .filter(survey__contract=contract, service=cs.service)
                        .order_by('-survey__date_conducted')
                        .values_list('score', flat=True)[:2]
                    )
                    if len(s_scores) >= 2 and s_scores[0] < 7 and s_scores[1] < 7:
                        services_at_risk.append(cs.service.name)
                urgent_list.append({
                    'client': contract.client.name,
                    'branch': contract.client.branch.name if contract.client.branch else '—',
                    'scores': [recent[0].nps_score, recent[1].nps_score],
                    'dates': [
                        recent[0].date_conducted.strftime('%d/%m/%y'),
                        recent[1].date_conducted.strftime('%d/%m/%y'),
                    ],
                    'services': services_at_risk,
                })

        # --- Pontos Fortes e Melhorias ---
        top_strengths = list(
            Strength.objects
            .filter(survey__in=surveys)
            .annotate(mentions=Count('survey'))
            .order_by('-mentions')
            .values('name', 'mentions')[:10]
        )
        top_improvements = list(
            Improvement.objects
            .filter(survey__in=surveys)
            .annotate(mentions=Count('survey'))
            .order_by('-mentions')
            .values('name', 'mentions')[:10]
        )

        # --- Filiais para o filtro ---
        if user.is_manager():
            filiais = list(user.branch.filter(is_active=True).order_by('name'))
        else:
            filiais = list(Filial.objects.filter(is_active=True).order_by('name'))

        context = {
            # Filtros
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
            'date_from_display': date_from.strftime('%d/%m/%Y'),
            'date_to_display': date_to.strftime('%d/%m/%Y'),
            'preset': preset,
            'filial_id': filial_id,
            'porte': porte,
            'filiais': filiais,
            # KPIs
            'nps_geral': nps_geral,
            'nps_geral_label': nps_geral_label,
            'nps_geral_badge': nps_geral_badge,
            'total_pesquisas': total,
            'empresas_avaliadas': empresas_avaliadas,
            'pct_promotores': pct_p,
            'pct_neutros': pct_n,
            'pct_detratores': pct_d,
            # Charts JSON
            'monthly_labels_json': json.dumps(monthly_labels),
            'monthly_nps_json': json.dumps(monthly_nps),
            'filial_labels_json': json.dumps([f['name'] for f in filial_chart_sorted]),
            'filial_nps_json': json.dumps([f['nps'] for f in filial_chart_sorted]),
            'filial_colors_json': json.dumps([_nps_chart_color(f['nps']) for f in filial_chart_sorted]),
            'porte_labels_json': json.dumps([p['name'] for p in porte_chart]),
            'porte_nps_json': json.dumps([p['nps'] for p in porte_chart]),
            'porte_colors_json': json.dumps([_nps_chart_color(p['nps']) for p in porte_chart]),
            'service_labels_json': json.dumps([s['name'] for s in service_chart_sorted]),
            'service_nps_json': json.dumps([s['nps'] for s in service_chart_sorted]),
            'service_colors_json': json.dumps([_nps_chart_color(s['nps']) for s in service_chart_sorted]),
            # Rankings
            'best_clients': best_clients,
            'worst_clients': worst_clients,
            'filial_ranking': filial_ranking,
            'urgent_list': urgent_list,
            # Qualitative
            'top_strengths': top_strengths,
            'top_improvements': top_improvements,
            'strengths_labels_json': json.dumps([s['name'] for s in top_strengths]),
            'strengths_values_json': json.dumps([s['mentions'] for s in top_strengths]),
            'improvements_labels_json': json.dumps([i['name'] for i in top_improvements]),
            'improvements_values_json': json.dumps([i['mentions'] for i in top_improvements]),
        }
        return render(request, self.template_name, context)
