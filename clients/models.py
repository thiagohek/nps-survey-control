from django.db import models


class Client(models.Model):
    class Size(models.TextChoices):
        SMALL = 'S', 'Pequeno'
        MEDIUM = 'M', 'Médio'
        LARGE = 'L', 'Grande'

    FREQUENCY_MAP = {'S': 90, 'M': 60, 'L': 30}

    name = models.CharField('Razão Social', max_length=300)
    cnpj = models.CharField('CNPJ', max_length=18, unique=True)
    contact_name = models.CharField('Nome do Contato', max_length=200, blank=True)
    contact_phone = models.CharField('Telefone', max_length=20, blank=True)
    contact_email = models.EmailField('E-mail', blank=True)
    size = models.CharField('Porte', max_length=1, choices=Size.choices)
    branch = models.ForeignKey(
        'organizations.Filial',
        on_delete=models.PROTECT,
        related_name='clients',
        verbose_name='Filial',
    )
    services = models.ManyToManyField(
        'organizations.Service',
        through='ClientService',
        related_name='clients',
        verbose_name='Serviços Contratados',
    )
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def survey_frequency_days(self):
        return self.FREQUENCY_MAP[self.size]

    @property
    def active_contract(self):
        """Retorna o contrato ativo do cliente, ou None."""
        return self.contracts.filter(status='active').first()

    @property
    def has_active_contract(self):
        return self.contracts.filter(status='active').exists()

    @property
    def active_services(self):
        """Retorna apenas os serviços ativos do cliente."""
        return self.services.filter(clientservice__is_active=True)


class ClientService(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    service = models.ForeignKey(
        'organizations.Service',
        on_delete=models.PROTECT,
        verbose_name='Serviço',
    )
    start_date = models.DateField('Data de Contratação', auto_now_add=True)
    end_date = models.DateField('Data de Cancelamento', null=True, blank=True)
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Serviço do Cliente'
        verbose_name_plural = 'Serviços do Cliente'
        unique_together = ['client', 'service']

    def __str__(self):
        status = 'Ativo' if self.is_active else 'Cancelado'
        return f'{self.service.name} ({status})'
