from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UserAsaasAccountTests(TestCase):
    def test_pode_receber_split_automatico_false_by_default(self):
        user = User.objects.create_user(email="foto@example.com", password="senha-segura-123")
        self.assertFalse(user.pode_receber_split_automatico)

    def test_pode_receber_split_automatico_true_when_aprovada(self):
        user = User.objects.create_user(email="foto2@example.com", password="senha-segura-123")
        user.asaas_account_status = User.ASAAS_STATUS_APROVADA
        user.save()
        self.assertTrue(user.pode_receber_split_automatico)

    def test_pode_receber_split_automatico_false_when_rejeitada(self):
        user = User.objects.create_user(email="foto3@example.com", password="senha-segura-123")
        user.asaas_account_status = User.ASAAS_STATUS_REJEITADA
        user.save()
        self.assertFalse(user.pode_receber_split_automatico)
