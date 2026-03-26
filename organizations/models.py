from django.db import models


class Filial(models.Model):
    name = models.CharField('Nome', max_length=200)
    code = models.CharField('Código', max_length=20, unique=True)
    address = models.TextField('Endereço', blank=True)
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Filial'
        verbose_name_plural = 'Filiais'
        ordering = ['name']

    def __str__(self):
        return f'{self.code} - {self.name}'


class Service(models.Model):
    name = models.CharField('Nome', max_length=200, unique=True)
    description = models.TextField('Descrição', blank=True)
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'
        ordering = ['name']

    def __str__(self):
        return self.name
