from django.db import models

from jobs.models import Job


class Pagamento(models.Model):
    STATUS_PENDENTE = "PENDENTE"
    STATUS_CONFIRMADO = "CONFIRMADO"
    STATUS_CHOICES = [
        (STATUS_PENDENTE, "Pendente"),
        (STATUS_CONFIRMADO, "Confirmado"),
    ]

    CONFIRMADO_MANUAL = "MANUAL"
    CONFIRMADO_WEBHOOK = "WEBHOOK"
    CONFIRMADO_POR_CHOICES = [
        (CONFIRMADO_MANUAL, "Manual"),
        (CONFIRMADO_WEBHOOK, "Webhook do gateway"),
    ]

    METODO_PIX = "PIX"
    METODO_BOLETO = "BOLETO"
    METODO_CARTAO = "CARTAO"
    METODO_CHOICES = [
        (METODO_PIX, "Pix"),
        (METODO_BOLETO, "Boleto"),
        (METODO_CARTAO, "Cartao"),
    ]

    job = models.OneToOneField(
        Job,
        on_delete=models.CASCADE,
        related_name="pagamento",
    )
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    confirmado_por = models.CharField(max_length=20, choices=CONFIRMADO_POR_CHOICES, blank=True)
    confirmado_em = models.DateTimeField(null=True, blank=True)
    metodo = models.CharField(max_length=10, choices=METODO_CHOICES, blank=True)
    provider_payment_id = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pagamento - job #{self.job_id} ({self.status})"

    def confirmar(self, origem, metodo="", provider_payment_id=""):
        from django.utils import timezone

        self.status = self.STATUS_CONFIRMADO
        self.confirmado_por = origem
        self.confirmado_em = timezone.now()
        if metodo:
            self.metodo = metodo
        if provider_payment_id:
            self.provider_payment_id = provider_payment_id
        self.save()

        portal = getattr(self.job, "portal_entrega", None)
        if portal:
            portal.status = portal.STATUS_LIBERADO
            portal.save()

        self.job.status = self.job.STATUS_ENTREGUE
        self.job.save()
