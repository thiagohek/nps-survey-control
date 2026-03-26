# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        DIRECTOR = 'DIRECTOR', 'Diretor'
        MANAGER = 'MANAGER', 'Gerente'
        RESEARCHER = 'RESEARCHER', 'Pesquisador'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.RESEARCHER)

    branch = models.ManyToManyField('organizations.Filial', blank=True, related_name='users')

    def is_director(self):
        return self.role == self.Role.DIRECTOR

    def is_manager(self):
        return self.role == self.Role.MANAGER

    def is_researcher(self):
        return self.role == self.Role.RESEARCHER

    def __str__(self):
        return self.username