from django.conf import settings
from django.db import models

from orcamentos.models import Orcamento


def arquivo_foto_upload_path(instance, filename):
    return f"jobs/{instance.job_id}/{instance.tipo}/{filename}"


class Job(models.Model):
    STATUS_ORCAMENTO_APROVADO = "ORCAMENTO_APROVADO"
    STATUS_CONTRATO_PENDENTE = "CONTRATO_PENDENTE"
    STATUS_CONTRATO_ASSINADO = "CONTRATO_ASSINADO"
    STATUS_EM_PRODUCAO = "EM_PRODUCAO"
    STATUS_AGUARDANDO_SELECAO = "AGUARDANDO_SELECAO"
    STATUS_SELECAO_CONCLUIDA = "SELECAO_CONCLUIDA"
    STATUS_EM_EDICAO = "EM_EDICAO"
    STATUS_AGUARDANDO_PAGAMENTO = "AGUARDANDO_PAGAMENTO"
    STATUS_ENTREGUE = "ENTREGUE"
    STATUS_CONCLUIDO = "CONCLUIDO"
    STATUS_CHOICES = [
        (STATUS_ORCAMENTO_APROVADO, "Orcamento aprovado"),
        (STATUS_CONTRATO_PENDENTE, "Contrato pendente"),
        (STATUS_CONTRATO_ASSINADO, "Contrato assinado"),
        (STATUS_EM_PRODUCAO, "Em producao"),
        (STATUS_AGUARDANDO_SELECAO, "Aguardando selecao"),
        (STATUS_SELECAO_CONCLUIDA, "Selecao concluida"),
        (STATUS_EM_EDICAO, "Em edicao"),
        (STATUS_AGUARDANDO_PAGAMENTO, "Aguardando pagamento"),
        (STATUS_ENTREGUE, "Entregue"),
        (STATUS_CONCLUIDO, "Concluido"),
    ]

    fotografo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="jobs",
    )
    cliente = models.ForeignKey(
        "clients.Cliente",
        on_delete=models.CASCADE,
        related_name="jobs",
    )
    orcamento = models.OneToOneField(
        Orcamento,
        on_delete=models.PROTECT,
        related_name="job",
    )
    titulo = models.CharField(max_length=150, blank=True)
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_ORCAMENTO_APROVADO,
    )
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.titulo or f"Job #{self.pk}"


class ArquivoFoto(models.Model):
    TIPO_BRUTA = "BRUTA"
    TIPO_EDITADA = "EDITADA"
    TIPO_CHOICES = [
        (TIPO_BRUTA, "Bruta"),
        (TIPO_EDITADA, "Editada"),
    ]

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="arquivos",
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    arquivo = models.FileField(upload_to=arquivo_foto_upload_path)
    thumbnail = models.ImageField(upload_to=arquivo_foto_upload_path, blank=True, null=True)
    arquivo_protegido = models.ImageField(upload_to=arquivo_foto_upload_path, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return f"{self.tipo} - job #{self.job_id}"
