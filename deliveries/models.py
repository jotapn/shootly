import uuid

from django.db import models

from jobs.models import ArquivoFoto, Job


class Selecao(models.Model):
    STATUS_PENDENTE = "PENDENTE"
    STATUS_CONCLUIDA = "CONCLUIDA"
    STATUS_CHOICES = [
        (STATUS_PENDENTE, "Pendente"),
        (STATUS_CONCLUIDA, "Concluida"),
    ]

    job = models.OneToOneField(
        Job,
        on_delete=models.CASCADE,
        related_name="selecao",
    )
    link_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    concluida_em = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Selecao - job #{self.job_id}"

    def concluir(self):
        from django.utils import timezone

        self.status = self.STATUS_CONCLUIDA
        self.concluida_em = timezone.now()
        self.save()

        self.job.status = self.job.STATUS_SELECAO_CONCLUIDA
        self.job.save()


class SelecaoItem(models.Model):
    selecao = models.ForeignKey(
        Selecao,
        on_delete=models.CASCADE,
        related_name="itens",
    )
    arquivo_foto = models.ForeignKey(
        ArquivoFoto,
        on_delete=models.CASCADE,
        related_name="itens_selecao",
    )
    selecionado = models.BooleanField(default=False)

    class Meta:
        unique_together = ("selecao", "arquivo_foto")

    def __str__(self):
        return f"{self.arquivo_foto} - selecionado={self.selecionado}"


class PortalEntrega(models.Model):
    STATUS_BLOQUEADO = "BLOQUEADO"
    STATUS_LIBERADO = "LIBERADO"
    STATUS_CHOICES = [
        (STATUS_BLOQUEADO, "Bloqueado"),
        (STATUS_LIBERADO, "Liberado"),
    ]

    job = models.OneToOneField(
        Job,
        on_delete=models.CASCADE,
        related_name="portal_entrega",
    )
    link_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_BLOQUEADO)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Portal de entrega - job #{self.job_id}"
