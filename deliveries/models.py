import uuid

from django.conf import settings
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
    max_fotos = models.PositiveIntegerField(null=True, blank=True)

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


class ConfiguracaoMarcaDagua(models.Model):
    MODO_UNICO = "unico"
    MODO_GRADE = "grade"
    MODO_CHOICES = [
        (MODO_UNICO, "Posição única"),
        (MODO_GRADE, "Grade (repetir em toda a foto)"),
    ]

    POSICAO_CENTRO = "centro"
    POSICAO_SUPERIOR_ESQ = "superior_esq"
    POSICAO_SUPERIOR_DIR = "superior_dir"
    POSICAO_INFERIOR_ESQ = "inferior_esq"
    POSICAO_INFERIOR_DIR = "inferior_dir"
    POSICAO_CHOICES = [
        (POSICAO_CENTRO, "Centro"),
        (POSICAO_SUPERIOR_ESQ, "Superior esquerdo"),
        (POSICAO_SUPERIOR_DIR, "Superior direito"),
        (POSICAO_INFERIOR_ESQ, "Inferior esquerdo"),
        (POSICAO_INFERIOR_DIR, "Inferior direito"),
    ]

    fotografo = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="marca_dagua",
    )
    arquivo_png = models.ImageField(upload_to="marcas_dagua/")
    opacidade = models.PositiveSmallIntegerField(default=50)
    tamanho_pct = models.PositiveSmallIntegerField(default=20)
    modo = models.CharField(max_length=10, choices=MODO_CHOICES, default=MODO_UNICO)
    # campos modo único
    posicao = models.CharField(max_length=20, choices=POSICAO_CHOICES, default=POSICAO_INFERIOR_DIR)
    # campos modo grade
    rotacao = models.SmallIntegerField(default=-30)
    espacamento_pct = models.PositiveSmallIntegerField(default=10)

    def __str__(self):
        return f"Marca d'água de {self.fotografo}"
