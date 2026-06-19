from django.contrib.auth import get_user_model
from django.test import TestCase

from clients.models import Cliente

User = get_user_model()


class ClienteModelTests(TestCase):
    def setUp(self):
        self.fotografo = User.objects.create_user(
            email="foto@example.com", password="senha-segura-123"
        )

    def test_str_returns_nome(self):
        cliente = Cliente.objects.create(fotografo=self.fotografo, nome="Escritorio XYZ")
        self.assertEqual(str(cliente), "Escritorio XYZ")

    def test_cliente_requires_fotografo(self):
        with self.assertRaises(Exception):
            Cliente.objects.create(nome="Sem fotografo")

    def test_default_ordering_is_by_nome(self):
        Cliente.objects.create(fotografo=self.fotografo, nome="Zeta Arquitetura")
        Cliente.objects.create(fotografo=self.fotografo, nome="Alfa Arquitetura")
        nomes = list(Cliente.objects.values_list("nome", flat=True))
        self.assertEqual(nomes, ["Alfa Arquitetura", "Zeta Arquitetura"])

    def test_cascade_delete_when_fotografo_removed(self):
        Cliente.objects.create(fotografo=self.fotografo, nome="Cliente Teste")
        self.fotografo.delete()
        self.assertEqual(Cliente.objects.count(), 0)
