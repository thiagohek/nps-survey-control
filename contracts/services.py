from datetime import timedelta

from django.utils import timezone

from .models import Contract, ContractService


FREQUENCY_MAP = {'S': 30, 'M': 60, 'L': 90}


def get_frequency(size):
    """Retorna a frequência de pesquisa em dias baseada no porte."""
    return FREQUENCY_MAP[size]


def create_contract(client, services, start_date=None):
    """
    Cria um novo contrato para o cliente com os servicos informados.
    Valida que não existe contrato ativo para o cliente.
    """
    if Contract.objects.filter(client=client, status=Contract.Status.ACTIVE).exists():
        raise ValueError('O cliente já possui um contrato ativo. Encerre-o antes de criar um novo.')

    if start_date is None:
        start_date = timezone.now().date()

    contract = Contract.objects.create(
        client=client,
        start_date=start_date,
        status=Contract.Status.ACTIVE,
        company_size=client.size,
        survey_frequency_days=get_frequency(client.size),
    )

    for service in services:
        ContractService.objects.create(
            contract=contract,
            service=service,
        )

    return contract


def close_contract(contract, end_date=None):
    """
    Encerra um contrato. Define status como 'closed' e preenche end_date.
    Remove agendamento pendente.
    """
    if contract.status == Contract.Status.CLOSED:
        raise ValueError('Este contrato já está encerrado.')

    if end_date is None:
        end_date = timezone.now().date()

    contract.status = Contract.Status.CLOSED
    contract.end_date = end_date
    contract.save()

    # Remover agendamento pendente
    from schedule.models import ScheduledSurvey
    ScheduledSurvey.objects.filter(
        contract=contract,
        status=ScheduledSurvey.Status.PENDING,
    ).delete()

    return contract


def generate_nps_surveys():
    """
    Verifica contratos ativos e cria/atualiza agendamentos de pesquisa
    para aqueles cujo intervalo já passou.
    Deve ser executado diariamente via management command.
    """
    from schedule.models import ScheduledSurvey

    today = timezone.now().date()
    contracts = Contract.objects.filter(status=Contract.Status.ACTIVE)
    created_count = 0

    for contract in contracts:
        should_schedule = False

        if not contract.last_survey_date:
            # Nunca houve pesquisa - agendar baseado na data de início
            next_date = contract.start_date + timedelta(days=contract.survey_frequency_days)
            if today >= contract.start_date:
                should_schedule = True
                scheduled_date = max(next_date, today)
        else:
            # Já houve pesquisa - verificar se intervalo passou
            next_date = contract.last_survey_date + timedelta(days=contract.survey_frequency_days)
            if today >= next_date:
                should_schedule = True
                scheduled_date = next_date

        if should_schedule:
            _, created = ScheduledSurvey.objects.update_or_create(
                contract=contract,
                defaults={
                    'scheduled_date': scheduled_date,
                    'status': ScheduledSurvey.Status.PENDING,
                },
            )
            if created:
                created_count += 1

    return created_count
