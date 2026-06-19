from django.contrib.auth import get_user_model
from django.test import TestCase

from clients.models import Cliente
from contracts.models import Contrato
from deliveries.models import PortalEntrega, Selecao
from jobs.models import Job
from orcamentos.models import Orcamento
from payments.models import Pagamento

User = get_user_model()


class FullJobLifecycleTests(TestCase):
    def test_job_flows_from_orcamento_to_pagamento_confirmado(self):
        fotografo = User.objects.create_user(email="foto@example.com", password="senha-segura-123")
        cliente = Cliente.objects.create(fotografo=fotografo, nome="Escritorio XYZ")

        orcamento = Orcamento.objects.create(fotografo=fotografo, cliente=cliente, valor_total=3000)
        orcamento.aprovar()

        job = Job.objects.create(fotografo=fotografo, cliente=cliente, orcamento=orcamento, valor_total=3000)
        self.assertEqual(job.status, Job.STATUS_ORCAMENTO_APROVADO)

        contrato = Contrato.objects.create(job=job, conteudo="Termos do contrato.")
        contrato.assinar(nome="Joao Arquiteto", cpf="000.000.000-00", ip="200.10.20.30")
        job.refresh_from_db()
        self.assertEqual(job.status, Job.STATUS_CONTRATO_ASSINADO)

        selecao = Selecao.objects.create(job=job)
        selecao.concluir()
        job.refresh_from_db()
        self.assertEqual(job.status, Job.STATUS_SELECAO_CONCLUIDA)

        portal = PortalEntrega.objects.create(job=job)
        self.assertEqual(portal.status, PortalEntrega.STATUS_BLOQUEADO)

        pagamento = Pagamento.objects.create(job=job, valor=3000)
        pagamento.confirmar(
            origem=Pagamento.CONFIRMADO_WEBHOOK,
            metodo=Pagamento.METODO_PIX,
            provider_payment_id="asaas_999",
        )

        job.refresh_from_db()
        portal.refresh_from_db()
        self.assertEqual(job.status, Job.STATUS_ENTREGUE)
        self.assertEqual(portal.status, PortalEntrega.STATUS_LIBERADO)
