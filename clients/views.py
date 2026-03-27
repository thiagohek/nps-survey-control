import csv
import io

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.db.models import Avg
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from accounts.mixins import ResearcherOrDirectorMixin
from contracts.models import Contract, ContractService
from organizations.models import Filial
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

        contract_status = self.request.GET.get('contract_status')
        if contract_status == 'active':
            qs = qs.filter(contracts__status=Contract.Status.ACTIVE).distinct()
        elif contract_status == 'no_active':
            qs = qs.exclude(contracts__status=Contract.Status.ACTIVE).distinct()

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


class ClientImportView(ResearcherOrDirectorMixin, LoginRequiredMixin, View):
    template_name = 'clients/client_import.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        upload = request.FILES.get('file')
        if not upload:
            return render(request, self.template_name, {'error': 'Nenhum arquivo enviado.'})

        name = upload.name.lower()
        if name.endswith('.csv'):
            rows = self._parse_csv(upload)
        elif name.endswith('.xlsx'):
            rows = self._parse_xlsx(upload)
        else:
            return render(request, self.template_name, {'error': 'Formato inválido. Envie um arquivo .csv ou .xlsx.'})

        created, skipped, errors = self._import_rows(rows)
        return render(request, self.template_name, {
            'result': True,
            'created': created,
            'skipped': skipped,
            'errors': errors,
        })

    def _parse_csv(self, upload):
        text = io.TextIOWrapper(upload, encoding='utf-8-sig')
        reader = csv.DictReader(text)
        return list(reader)

    def _parse_xlsx(self, upload):
        import openpyxl
        wb = openpyxl.load_workbook(upload, read_only=True, data_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        headers = [str(h).strip() if h is not None else '' for h in next(rows_iter)]
        result = []
        for row in rows_iter:
            result.append({headers[i]: (str(v).strip() if v is not None else '') for i, v in enumerate(row)})
        wb.close()
        return result

    def _import_rows(self, rows):
        REQUIRED = {'name', 'cnpj', 'size', 'branch'}
        VALID_SIZES = {'S', 'M', 'L'}
        created = 0
        skipped = 0
        errors = []

        for line_num, row in enumerate(rows, start=2):
            # Normaliza chaves
            row = {k.strip().lower(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}

            missing = REQUIRED - set(row.keys())
            if missing:
                errors.append({'linha': line_num, 'motivo': f'Colunas ausentes: {", ".join(missing)}'})
                continue

            name = row.get('name', '')
            cnpj = row.get('cnpj', '')
            size = row.get('size', '').upper()
            branch_code = row.get('branch', '')

            if not name or not cnpj or not size or not branch_code:
                errors.append({'linha': line_num, 'motivo': 'Campos obrigatórios vazios (name, cnpj, size, branch).'})
                continue

            if size not in VALID_SIZES:
                errors.append({'linha': line_num, 'motivo': f'Porte inválido: "{size}". Use S, M ou L.'})
                continue

            try:
                branch = Filial.objects.get(code=branch_code)
            except Filial.DoesNotExist:
                errors.append({'linha': line_num, 'motivo': f'Filial com código "{branch_code}" não encontrada.'})
                continue

            try:
                Client.objects.create(
                    name=name,
                    cnpj=cnpj,
                    size=size,
                    branch=branch,
                    contact_name=row.get('contact_name', ''),
                    contact_phone=row.get('contact_phone', ''),
                    contact_email=row.get('contact_email', ''),
                )
                created += 1
            except IntegrityError:
                skipped += 1

        return created, skipped, errors
