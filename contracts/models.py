from django.db import models


class Contract(models.Model):
    """Contrato entre a empresa e o cliente. Snapshot do estado do cliente."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Ativo'
        CLOSED = 'closed', 'Encerrado'

    SIZE_CHOICES = [
        ('S', 'Pequeno'),
        ('M', 'Médio'),
        ('L', 'Grande'),
    ]

    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.PROTECT,
        related_name='contracts',
        verbose_name='Cliente',
    )
    start_date = models.DateField('Data de Início')
    end_date = models.DateField('Data de Encerramento', null=True, blank=True)
    status = models.CharField(
        'Status',
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    company_size = models.CharField(
        'Porte na Contratação',
        max_length=1,
        choices=SIZE_CHOICES,
    )
    survey_frequency_days = models.IntegerField('Frequência de Pesquisa (dias)')
    last_survey_date = models.DateField(
        'Data da Última Pesquisa',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.client.name} - {self.start_date} ({self.get_status_display()})'

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE


class ContractService(models.Model):
    """Snapshot dos serviços contratados no momento da criação do contrato."""

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='contract_services',
        verbose_name='Contrato',
    )
    service = models.ForeignKey(
        'organizations.Service',
        on_delete=models.PROTECT,
        related_name='contract_services',
        verbose_name='Serviço',
    )

    class Meta:
        verbose_name = 'Serviço do Contrato'
        verbose_name_plural = 'Serviços do Contrato'
        unique_together = ['contract', 'service']

    def __str__(self):
        return f'{self.service.name}'
