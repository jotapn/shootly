from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    @property
    def is_active_plan(self):
        try:
            user_plan = self.user_plan
        except Exception:
            return False
        return user_plan.status == "ACTIVE"

    ASAAS_STATUS_PENDENTE = "PENDENTE"
    ASAAS_STATUS_APROVADA = "APROVADA"
    ASAAS_STATUS_REJEITADA = "REJEITADA"
    ASAAS_STATUS_CHOICES = [
        (ASAAS_STATUS_PENDENTE, "Pendente"),
        (ASAAS_STATUS_APROVADA, "Aprovada"),
        (ASAAS_STATUS_REJEITADA, "Rejeitada"),
    ]

    asaas_account_id = models.CharField(max_length=64, blank=True)
    asaas_account_status = models.CharField(
        max_length=20,
        choices=ASAAS_STATUS_CHOICES,
        default=ASAAS_STATUS_PENDENTE,
    )

    @property
    def pode_receber_split_automatico(self):
        return self.asaas_account_status == self.ASAAS_STATUS_APROVADA

    def __str__(self):
        return self.email

