from django.conf import settings
from django.db import models


class Cliente(models.Model):
    fotografo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clientes",
    )
    nome = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    empresa = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome
