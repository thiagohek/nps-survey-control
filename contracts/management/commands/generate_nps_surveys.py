from django.core.management.base import BaseCommand
from contracts.services import generate_nps_surveys


class Command(BaseCommand):
    help = 'Gera agendamentos de pesquisa NPS para contratos ativos cujo intervalo já passou.'

    def handle(self, *args, **options):
        count = generate_nps_surveys()
        self.stdout.write(
            self.style.SUCCESS(f'{count} agendamento(s) de pesquisa criado(s).')
        )
