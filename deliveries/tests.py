from django.contrib.auth import get_user_model
from django.test import TestCase

from clients.models import Cliente
from deliveries.models import PortalEntrega, Selecao, SelecaoItem
from jobs.models import ArquivoFoto, Job
from orcamentos.models import Orcamento

User = get_user_model()


class DeliveriesModelTests(TestCase):
    def setUp(self):
        self.fotografo = User.objects.create_user(
            email="foto@example.com", password="senha-segura-123"
        )
        self.cliente = Cliente.objects.create(fotografo=self.fotografo, nome="Escritorio XYZ")
        self.orcamento = Orcamento.objects.create(
            fotografo=self.fotografo, cliente=self.cliente, valor_total=2000
        )
        self.job = Job.objects.create(
            fotografo=self.fotografo, cliente=self.cliente, orcamento=self.orcamento, valor_total=2000
        )

    def test_portal_entrega_starts_bloqueado_by_default(self):
        # Default de seguranca critico: o portal NUNCA comeca liberado -
        # so abre por uma acao explicita (pagamento confirmado)
        portal = PortalEntrega.objects.create(job=self.job)
        self.assertEqual(portal.status, PortalEntrega.STATUS_BLOQUEADO)

    def test_selecao_concluir_updates_job_status(self):
        selecao = Selecao.objects.create(job=self.job)
        selecao.concluir()
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, Job.STATUS_SELECAO_CONCLUIDA)
        self.assertIsNotNone(selecao.concluida_em)

    def test_selecao_item_unique_together_prevents_duplicate(self):
        selecao = Selecao.objects.create(job=self.job)
        arquivo = ArquivoFoto.objects.create(job=self.job, tipo=ArquivoFoto.TIPO_BRUTA)
        SelecaoItem.objects.create(selecao=selecao, arquivo_foto=arquivo, selecionado=True)
        with self.assertRaises(Exception):
            SelecaoItem.objects.create(selecao=selecao, arquivo_foto=arquivo, selecionado=False)

    def test_portal_link_token_unique_across_jobs(self):
        portal1 = PortalEntrega.objects.create(job=self.job)
        orcamento2 = Orcamento.objects.create(
            fotografo=self.fotografo, cliente=self.cliente, valor_total=500
        )
        job2 = Job.objects.create(
            fotografo=self.fotografo, cliente=self.cliente, orcamento=orcamento2, valor_total=500
        )
        portal2 = PortalEntrega.objects.create(job=job2)
        self.assertNotEqual(portal1.link_token, portal2.link_token)
