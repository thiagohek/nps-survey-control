from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Strength(models.Model):
    """Ponto forte da empresa (cadastrado pelo admin)."""
    name = models.CharField('Descrição', max_length=300, unique=True)
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Ponto Forte'
        verbose_name_plural = 'Pontos Fortes'
        ordering = ['name']

    def __str__(self):
        return self.name


class Improvement(models.Model):
    """Ponto a melhorar (cadastrado pelo admin)."""
    name = models.CharField('Descrição', max_length=300, unique=True)
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Ponto a Melhorar'
        verbose_name_plural = 'Pontos a Melhorar'
        ordering = ['name']

    def __str__(self):
        return self.name


class Survey(models.Model):
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='surveys',
        verbose_name='Cliente',
    )
    date_conducted = models.DateField('Data da Pesquisa')
    respondent_name = models.CharField('Nome do Respondente', max_length=200)
    respondent_role = models.CharField('Cargo do Respondente', max_length=200)
    nps_score = models.IntegerField(
        'Nota Geral (NPS)',
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text='De 0 a 10, o cliente indicaria a empresa?',
    )
    strengths = models.ManyToManyField(
        Strength,
        blank=True,
        verbose_name='Pontos Fortes',
    )
    improvements = models.ManyToManyField(
        Improvement,
        blank=True,
        verbose_name='Pontos a Melhorar',
    )
    comments = models.TextField('Comentários', blank=True)
    is_historical = models.BooleanField(
        'Pesquisa Histórica',
        default=False,
        help_text='Marque se esta pesquisa foi realizada antes do sistema existir.',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='surveys_created',
        verbose_name='Pesquisador',
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Pesquisa'
        verbose_name_plural = 'Pesquisas'
        ordering = ['-date_conducted']
        unique_together = ['client', 'date_conducted']

    def __str__(self):
        return f'{self.client.name} - {self.date_conducted}'


class ServiceScore(models.Model):
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='service_scores',
        verbose_name='Pesquisa',
    )
    service = models.ForeignKey(
        'organizations.Service',
        on_delete=models.PROTECT,
        verbose_name='Serviço',
    )
    score = models.IntegerField(
        'Nota',
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )

    class Meta:
        verbose_name = 'Nota por Serviço'
        verbose_name_plural = 'Notas por Serviço'
        unique_together = ['survey', 'service']

    def __str__(self):
        return f'{self.service.name}: {self.score}'
