from django.contrib.auth import get_user_model
from django.test import TestCase

from clients.models import Cliente
from deliveries.models import PortalEntrega
from jobs.models import Job
from orcamentos.models import Orcamento
from payments.models import Pagamento

User = get_user_model()


class PagamentoModelTests(TestCase):
    def setUp(self):
        self.fotografo = User.objects.create_user(
            email="foto@example.com", password="senha-segura-123"
        )
        self.cliente = Cliente.objects.create(fotografo=self.fotografo, nome="Escritorio XYZ")
        self.orcamento = Orcamento.objects.create(
            fotografo=self.fotografo, cliente=self.cliente, valor_total=1800
        )
        self.job = Job.objects.create(
            fotografo=self.fotografo, cliente=self.cliente, orcamento=self.orcamento, valor_total=1800
        )
        self.portal = PortalEntrega.objects.create(job=self.job)
        self.pagamento = Pagamento.objects.create(job=self.job, valor=1800)

    def test_pagamento_starts_pendente(self):
        self.assertEqual(self.pagamento.status, Pagamento.STATUS_PENDENTE)

    def test_confirmar_manual_unlocks_portal(self):
        self.pagamento.confirmar(origem=Pagamento.CONFIRMADO_MANUAL)
        self.portal.refresh_from_db()
        self.assertEqual(self.portal.status, PortalEntrega.STATUS_LIBERADO)

    def test_confirmar_webhook_unlocks_portal_same_as_manual(self):
        # Confirma a unificacao decidida: a origem nao muda o resultado
        self.pagamento.confirmar(
            origem=Pagamento.CONFIRMADO_WEBHOOK,
            metodo=Pagamento.METODO_PIX,
            provider_payment_id="asaas_123",
        )
        self.portal.refresh_from_db()
        self.assertEqual(self.portal.status, PortalEntrega.STATUS_LIBERADO)
        self.assertEqual(self.pagamento.confirmado_por, Pagamento.CONFIRMADO_WEBHOOK)
        self.assertEqual(self.pagamento.provider_payment_id, "asaas_123")

    def test_confirmar_updates_job_status_to_entregue(self):
        self.pagamento.confirmar(origem=Pagamento.CONFIRMADO_MANUAL)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, Job.STATUS_ENTREGUE)

    def test_confirmar_records_confirmado_em(self):
        self.assertIsNone(self.pagamento.confirmado_em)
        self.pagamento.confirmar(origem=Pagamento.CONFIRMADO_MANUAL)
        self.assertIsNotNone(self.pagamento.confirmado_em)

    def test_pagamento_without_portal_entrega_does_not_raise(self):
        orcamento2 = Orcamento.objects.create(
            fotografo=self.fotografo, cliente=self.cliente, valor_total=500
        )
        job2 = Job.objects.create(
            fotografo=self.fotografo, cliente=self.cliente, orcamento=orcamento2, valor_total=500
        )
        pagamento2 = Pagamento.objects.create(job=job2, valor=500)
        pagamento2.confirmar(origem=Pagamento.CONFIRMADO_MANUAL)
        self.assertEqual(pagamento2.status, Pagamento.STATUS_CONFIRMADO)
