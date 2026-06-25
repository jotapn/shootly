from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clients.models import Cliente
from deliveries.models import (
    GrupoBracketing,
    GrupoBracketingFoto,
    PortalEntrega,
    Selecao,
    SelecaoItem,
)
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

    def test_grupo_bracketing_item_counts_as_one_selection(self):
        fotos = [
            ArquivoFoto.objects.create(job=self.job, tipo=ArquivoFoto.TIPO_BRUTA)
            for _ in range(3)
        ]
        grupo = GrupoBracketing.objects.create(job=self.job, capa=fotos[0], nome="HDR sala")
        GrupoBracketingFoto.objects.bulk_create([
            GrupoBracketingFoto(grupo=grupo, arquivo_foto=foto, ordem=index)
            for index, foto in enumerate(fotos)
        ])
        selecao = Selecao.objects.create(job=self.job, max_fotos=1)
        item = SelecaoItem.objects.create(selecao=selecao, grupo=grupo, selecionado=True)

        self.assertTrue(item.is_grupo)
        self.assertEqual(item.capa, fotos[0])
        self.assertEqual(item.quantidade_fotos, 3)
        self.assertEqual(selecao.itens.filter(selecionado=True).count(), 1)

    def test_selecao_create_inclui_grupo_e_ignora_fotos_internas(self):
        self.client.force_login(self.fotografo)
        self.job.status = Job.STATUS_EM_PRODUCAO
        self.job.quantidade_fotos_incluidas = 2
        self.job.save(update_fields=["status", "quantidade_fotos_incluidas"])
        fotos_grupo = [
            ArquivoFoto.objects.create(job=self.job, tipo=ArquivoFoto.TIPO_BRUTA)
            for _ in range(3)
        ]
        foto_individual = ArquivoFoto.objects.create(job=self.job, tipo=ArquivoFoto.TIPO_BRUTA)
        grupo = GrupoBracketing.objects.create(job=self.job, capa=fotos_grupo[0])
        GrupoBracketingFoto.objects.bulk_create([
            GrupoBracketingFoto(grupo=grupo, arquivo_foto=foto, ordem=index)
            for index, foto in enumerate(fotos_grupo)
        ])

        response = self.client.post(reverse("deliveries:selecao_create", args=[self.job.pk]))

        self.assertRedirects(response, reverse("jobs:detail", args=[self.job.pk]))
        selecao = self.job.selecao
        self.assertEqual(selecao.max_fotos, 2)
        self.assertEqual(selecao.itens.count(), 2)
        self.assertTrue(selecao.itens.filter(grupo=grupo).exists())
        self.assertTrue(selecao.itens.filter(arquivo_foto=foto_individual).exists())
        for foto in fotos_grupo:
            self.assertFalse(selecao.itens.filter(arquivo_foto=foto).exists())

    def test_public_confirm_marks_group_item_as_selected(self):
        fotos = [
            ArquivoFoto.objects.create(job=self.job, tipo=ArquivoFoto.TIPO_BRUTA)
            for _ in range(3)
        ]
        grupo = GrupoBracketing.objects.create(job=self.job, capa=fotos[0])
        GrupoBracketingFoto.objects.bulk_create([
            GrupoBracketingFoto(grupo=grupo, arquivo_foto=foto, ordem=index)
            for index, foto in enumerate(fotos)
        ])
        selecao = Selecao.objects.create(job=self.job, max_fotos=1)
        item = SelecaoItem.objects.create(selecao=selecao, grupo=grupo)

        response = self.client.post(
            reverse("deliveries:public_selecao_confirm", args=[selecao.link_token]),
            {"selecionados": [str(item.id)]},
        )

        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        selecao.refresh_from_db()
        self.assertTrue(item.selecionado)
        self.assertEqual(selecao.status, Selecao.STATUS_CONCLUIDA)
