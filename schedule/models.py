from django.db import models
from django.utils import timezone


class ScheduledSurvey(models.Model):
    class Status(models.TextChoices):
        PENDING = 'P', 'Pendente'
        COMPLETED = 'C', 'Concluída'
        OVERDUE = 'O', 'Atrasada'

    contract = models.OneToOneField(
        'contracts.Contract',
        on_delete=models.CASCADE,
        related_name='scheduled_survey',
        verbose_name='Contrato',
    )
    scheduled_date = models.DateField('Data Agendada')
    status = models.CharField(
        'Status',
        max_length=1,
        choices=Status.choices,
        default=Status.PENDING,
    )
    last_survey = models.ForeignKey(
        'surveys.Survey',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_schedule',
        verbose_name='Última Pesquisa',
    )

    class Meta:
        verbose_name = 'Pesquisa Agendada'
        verbose_name_plural = 'Pesquisas Agendadas'
        ordering = ['scheduled_date']

    def __str__(self):
        return f'{self.contract.client.name} - {self.scheduled_date}'

    @property
    def is_overdue(self):
        return self.status == self.Status.PENDING and self.scheduled_date < timezone.now().date()
