import uuid

from django.conf import settings
from django.db import models


class Servico(models.Model):
    fotografo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="servicos",
    )
    nome = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    valor_padrao = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Orcamento(models.Model):
    STATUS_RASCUNHO = "RASCUNHO"
    STATUS_ENVIADO = "ENVIADO"
    STATUS_APROVADO = "APROVADO"
    STATUS_RECUSADO = "RECUSADO"
    STATUS_CHOICES = [
        (STATUS_RASCUNHO, "Rascunho"),
        (STATUS_ENVIADO, "Enviado"),
        (STATUS_APROVADO, "Aprovado"),
        (STATUS_RECUSADO, "Recusado"),
    ]

    fotografo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orcamentos",
    )
    cliente = models.ForeignKey(
        "clients.Cliente",
        on_delete=models.CASCADE,
        related_name="orcamentos",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_RASCUNHO)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    link_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    enviado_em = models.DateTimeField(null=True, blank=True)
    respondido_em = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Orcamento #{self.pk} - {self.cliente}"

    def aprovar(self):
        from django.utils import timezone

        self.status = self.STATUS_APROVADO
        self.respondido_em = timezone.now()
        self.save()


class OrcamentoItem(models.Model):
    orcamento = models.ForeignKey(
        Orcamento,
        on_delete=models.CASCADE,
        related_name="itens",
    )
    servico = models.ForeignKey(
        Servico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="itens_orcamento",
    )
    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.descricao
