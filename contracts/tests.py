import hashlib

from django.contrib.auth import get_user_model
from django.test import TestCase

from clients.models import Cliente
from contracts.models import Contrato
from jobs.models import Job
from orcamentos.models import Orcamento

User = get_user_model()


class ContratoModelTests(TestCase):
    def setUp(self):
        self.fotografo = User.objects.create_user(
            email="foto@example.com", password="senha-segura-123"
        )
        self.cliente = Cliente.objects.create(fotografo=self.fotografo, nome="Escritorio XYZ")

    def _criar_job(self, valor=2000):
        orcamento = Orcamento.objects.create(
            fotografo=self.fotografo, cliente=self.cliente, valor_total=valor
        )
        return Job.objects.create(
            fotografo=self.fotografo, cliente=self.cliente, orcamento=orcamento, valor_total=valor
        )

    def test_assinar_sets_status_to_assinado(self):
        job = self._criar_job()
        contrato = Contrato.objects.create(job=job, conteudo="Termos do contrato.")
        contrato.assinar(nome="Joao Arquiteto", cpf="000.000.000-00", ip="200.10.20.30")
        self.assertEqual(contrato.status, Contrato.STATUS_ASSINADO)

    def test_assinar_records_ip_and_timestamp(self):
        job = self._criar_job()
        contrato = Contrato.objects.create(job=job, conteudo="Termos do contrato.")
        contrato.assinar(nome="Joao Arquiteto", cpf="000.000.000-00", ip="200.10.20.30")
        self.assertEqual(contrato.assinatura_ip, "200.10.20.30")
        self.assertIsNotNone(contrato.assinatura_data)

    def test_hash_documento_matches_sha256_of_conteudo(self):
        job = self._criar_job()
        contrato = Contrato.objects.create(job=job, conteudo="Termos do contrato.")
        contrato.assinar(nome="Joao Arquiteto", cpf="000.000.000-00", ip="200.10.20.30")
        esperado = hashlib.sha256(contrato.conteudo.encode("utf-8")).hexdigest()
        self.assertEqual(contrato.hash_documento, esperado)

    def test_assinar_updates_job_status(self):
        job = self._criar_job()
        contrato = Contrato.objects.create(job=job, conteudo="Termos do contrato.")
        contrato.assinar(nome="Joao Arquiteto", cpf="000.000.000-00", ip="200.10.20.30")
        job.refresh_from_db()
        self.assertEqual(job.status, Job.STATUS_CONTRATO_ASSINADO)

    def test_different_conteudo_produces_different_hash(self):
        job1 = self._criar_job()
        job2 = self._criar_job()
        contrato1 = Contrato.objects.create(job=job1, conteudo="Texto A do contrato.")
        contrato2 = Contrato.objects.create(job=job2, conteudo="Texto B do contrato, diferente.")
        contrato1.assinar(nome="A", cpf="000", ip="1.1.1.1")
        contrato2.assinar(nome="A", cpf="000", ip="1.1.1.1")
        self.assertNotEqual(contrato1.hash_documento, contrato2.hash_documento)

    def test_assinar_called_twice_currently_overwrites_without_warning(self):
        # GAP DE SEGURANCA CONHECIDO: assinar() ainda nao impede ser
        # chamado de novo em um contrato ja assinado, e sobrescreve a
        # assinatura original sem aviso nem erro. Este teste documenta o
        # comportamento ATUAL. Quando a protecao for adicionada numa fase
        # futura, troque a ultima linha por assertRaises.
        job = self._criar_job()
        contrato = Contrato.objects.create(job=job, conteudo="Termos do contrato.")
        contrato.assinar(nome="Primeira pessoa", cpf="111", ip="1.1.1.1")
        primeiro_hash = contrato.hash_documento
        contrato.assinar(nome="Segunda pessoa", cpf="222", ip="2.2.2.2")
        self.assertEqual(contrato.assinatura_nome, "Segunda pessoa")
        self.assertEqual(contrato.hash_documento, primeiro_hash)
