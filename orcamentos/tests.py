from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clients.models import Cliente
from jobs.models import Job
from orcamentos.models import Orcamento, OrcamentoItem, Servico

User = get_user_model()


class OrcamentoModelTests(TestCase):
    def setUp(self):
        self.fotografo = User.objects.create_user(
            email="foto@example.com", password="senha-segura-123"
        )
        self.cliente = Cliente.objects.create(fotografo=self.fotografo, nome="Escritorio XYZ")

    def test_orcamento_starts_as_rascunho(self):
        orcamento = Orcamento.objects.create(
            fotografo=self.fotografo, cliente=self.cliente, valor_total=1500
        )
        self.assertEqual(orcamento.status, Orcamento.STATUS_RASCUNHO)

    def test_aprovar_changes_status_and_sets_respondido_em(self):
        orcamento = Orcamento.objects.create(
            fotografo=self.fotografo, cliente=self.cliente, valor_total=1500
        )
        self.assertIsNone(orcamento.respondido_em)
        orcamento.aprovar()
        orcamento.refresh_from_db()
        self.assertEqual(orcamento.status, Orcamento.STATUS_APROVADO)
        self.assertIsNotNone(orcamento.respondido_em)

    def test_link_token_is_unique_per_orcamento(self):
        o1 = Orcamento.objects.create(fotografo=self.fotografo, cliente=self.cliente, valor_total=100)
        o2 = Orcamento.objects.create(fotografo=self.fotografo, cliente=self.cliente, valor_total=200)
        self.assertNotEqual(o1.link_token, o2.link_token)

    def test_link_token_uses_uuid4(self):
        # UUID4 tem 122 bits de entropia - garante que ninguem adivinha o
        # token de outro orcamento incrementando ou pela ordem de criacao
        orcamento = Orcamento.objects.create(fotografo=self.fotografo, cliente=self.cliente, valor_total=100)
        self.assertEqual(orcamento.link_token.version, 4)

    def test_orcamento_item_survives_servico_deletion(self):
        servico = Servico.objects.create(fotografo=self.fotografo, nome="Ensaio externo", valor_padrao=800)
        orcamento = Orcamento.objects.create(fotografo=self.fotografo, cliente=self.cliente, valor_total=800)
        item = OrcamentoItem.objects.create(
            orcamento=orcamento, servico=servico, descricao="Ensaio externo", valor=800
        )
        servico.delete()
        item.refresh_from_db()
        self.assertIsNone(item.servico)
        self.assertEqual(OrcamentoItem.objects.count(), 1)

    def test_public_approve_copies_selection_terms_to_job(self):
        orcamento = Orcamento.objects.create(
            fotografo=self.fotografo,
            cliente=self.cliente,
            valor_total=1500,
            status=Orcamento.STATUS_ENVIADO,
            quantidade_fotos_incluidas=12,
            valor_foto_extra=80,
        )
        response = self.client.post(reverse("orcamentos:public_approve", args=[orcamento.link_token]))
        self.assertEqual(response.status_code, 200)

        job = Job.objects.get(orcamento=orcamento)
        self.assertEqual(job.quantidade_fotos_incluidas, 12)
        self.assertEqual(job.valor_foto_extra, 80)
        self.assertEqual(job.status, Job.STATUS_CONTRATO_PENDENTE)
