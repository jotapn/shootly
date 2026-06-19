import hashlib
import uuid

from django.db import models

from jobs.models import Job


class Contrato(models.Model):
    STATUS_PENDENTE = "PENDENTE"
    STATUS_ASSINADO = "ASSINADO"
    STATUS_CHOICES = [
        (STATUS_PENDENTE, "Pendente"),
        (STATUS_ASSINADO, "Assinado"),
    ]

    job = models.OneToOneField(
        Job,
        on_delete=models.CASCADE,
        related_name="contrato",
    )
    conteudo = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    link_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    assinatura_nome = models.CharField(max_length=120, blank=True)
    assinatura_cpf = models.CharField(max_length=20, blank=True)
    assinatura_ip = models.GenericIPAddressField(null=True, blank=True)
    assinatura_data = models.DateTimeField(null=True, blank=True)
    hash_documento = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contrato - job #{self.job_id}"

    def assinar(self, nome, cpf, ip):
        from django.utils import timezone

        self.assinatura_nome = nome
        self.assinatura_cpf = cpf
        self.assinatura_ip = ip
        self.assinatura_data = timezone.now()
        self.hash_documento = hashlib.sha256(self.conteudo.encode("utf-8")).hexdigest()
        self.status = self.STATUS_ASSINADO
        self.save()

        self.job.status = self.job.STATUS_CONTRATO_ASSINADO
        self.job.save()
