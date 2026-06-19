from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from clients.models import Cliente
from jobs.models import ArquivoFoto, Job
from orcamentos.models import Orcamento

User = get_user_model()


class JobModelTests(TestCase):
    def setUp(self):
        self.fotografo = User.objects.create_user(
            email="foto@example.com", password="senha-segura-123"
        )
        self.cliente = Cliente.objects.create(fotografo=self.fotografo, nome="Escritorio XYZ")
        self.orcamento = Orcamento.objects.create(
            fotografo=self.fotografo, cliente=self.cliente, valor_total=2000
        )

    def test_job_starts_with_orcamento_aprovado_status(self):
        job = Job.objects.create(
            fotografo=self.fotografo, cliente=self.cliente, orcamento=self.orcamento, valor_total=2000
        )
        self.assertEqual(job.status, Job.STATUS_ORCAMENTO_APROVADO)

    def test_orcamento_can_only_be_linked_to_one_job(self):
        Job.objects.create(
            fotografo=self.fotografo, cliente=self.cliente, orcamento=self.orcamento, valor_total=2000
        )
        with self.assertRaises(Exception):
            Job.objects.create(
                fotografo=self.fotografo, cliente=self.cliente, orcamento=self.orcamento, valor_total=2000
            )

    def test_arquivo_foto_upload_path_does_not_expose_fotografo_email(self):
        # O path do arquivo so usa o id do job, nunca dado do fotografo -
        # reduz informacao sensivel exposta em URLs de arquivo geradas
        job = Job.objects.create(
            fotografo=self.fotografo, cliente=self.cliente, orcamento=self.orcamento, valor_total=2000
        )
        arquivo = ArquivoFoto.objects.create(
            job=job,
            tipo=ArquivoFoto.TIPO_BRUTA,
            arquivo=SimpleUploadedFile("foto.jpg", b"conteudo-fake"),
        )
        self.assertIn(f"jobs/{job.id}/BRUTA/", arquivo.arquivo.name)
        self.assertNotIn(self.fotografo.email, arquivo.arquivo.name)
