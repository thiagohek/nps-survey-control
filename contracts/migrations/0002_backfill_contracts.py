"""
Data migration: cria contratos para clientes existentes e faz backfill
de Survey.contract e ScheduledSurvey.contract.
"""

from django.db import migrations
from django.utils import timezone


FREQUENCY_MAP = {'S': 30, 'M': 60, 'L': 90}


def backfill_contracts(apps, schema_editor):
    Client = apps.get_model('clients', 'Client')
    Contract = apps.get_model('contracts', 'Contract')
    ContractService = apps.get_model('contracts', 'ContractService')
    ClientService = apps.get_model('clients', 'ClientService')
    Survey = apps.get_model('surveys', 'Survey')
    ScheduledSurvey = apps.get_model('schedule', 'ScheduledSurvey')

    today = timezone.now().date()

    for client in Client.objects.all():
        surveys = Survey.objects.filter(client=client).order_by('date_conducted')
        earliest_survey = surveys.first()
        latest_survey = surveys.last()

        # Determinar start_date
        if earliest_survey:
            start_date = earliest_survey.date_conducted
        else:
            start_date = today

        # Criar contrato
        contract = Contract.objects.create(
            client=client,
            start_date=start_date,
            status='active',
            company_size=client.size,
            survey_frequency_days=FREQUENCY_MAP.get(client.size, 60),
            last_survey_date=latest_survey.date_conducted if latest_survey else None,
        )

        # Snapshot dos servicos ativos
        active_services = ClientService.objects.filter(client=client, is_active=True)
        for cs in active_services:
            ContractService.objects.create(
                contract=contract,
                service=cs.service,
            )

        # Backfill surveys
        surveys.update(contract=contract)

        # Backfill scheduled survey
        ScheduledSurvey.objects.filter(client=client).update(contract=contract)


def reverse_backfill(apps, schema_editor):
    Contract = apps.get_model('contracts', 'Contract')
    ContractService = apps.get_model('contracts', 'ContractService')
    Survey = apps.get_model('surveys', 'Survey')
    ScheduledSurvey = apps.get_model('schedule', 'ScheduledSurvey')

    # Limpar FKs de contract
    Survey.objects.all().update(contract=None)
    ScheduledSurvey.objects.all().update(contract=None)

    # Deletar contratos criados
    ContractService.objects.all().delete()
    Contract.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0001_initial'),
        ('clients', '0001_initial'),
        ('surveys', '0004_survey_contract_alter_survey_client'),
        ('schedule', '0003_scheduledsurvey_contract_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_contracts, reverse_backfill),
    ]
