from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from .models import Usuario
import pyotp
from django.utils import timezone
from datetime import timedelta

class DummyTest(TestCase):
    def test_dummy(self):
        self.assertEqual(1, 1)
        
class LoginTOTPTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = Usuario.objects.create(
            cedula=123456789,
            nombre="Test User",
            edad=30,
            celular="3001234567",
            password="$2b$12$KIXQ8kBv1x6h6s6j6s6j6uJj6uJj6uJj6uJj6uJj6uJj6uJj6uJj6",  # hash real de bcrypt
            totp_secret=pyotp.random_base32(),
            totp_confirmed=True
        )
        self.usuario.set_password("testpassword")  # Si tienes método personalizado
        self.usuario.save()
        self.totp = pyotp.TOTP(self.usuario.totp_secret)

    def test_login_success(self):
        code = self.totp.now()
        response = self.client.post(
            reverse('validar_password_usuario_api'),
            {
                "cedula": self.usuario.cedula,
                "password": "testpassword",
                "totp": code
            },
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)

    def test_login_wrong_totp(self):
        response = self.client.post(
            reverse('validar_password_usuario_api'),
            {
                "cedula": self.usuario.cedula,
                "password": "testpassword",
                "totp": "000000"
            },
            format='json'
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["message"], "Código TOTP inválido")

    def test_login_block_after_three_attempts(self):
        for _ in range(3):
            response = self.client.post(
                reverse('validar_password_usuario_api'),
                {
                    "cedula": self.usuario.cedula,
                    "password": "testpassword",
                    "totp": "000000"
                },
                format='json'
            )
        # Cuarto intento, debe estar bloqueado
        response = self.client.post(
            reverse('validar_password_usuario_api'),
            {
                "cedula": self.usuario.cedula,
                "password": "testpassword",
                "totp": "000000"
            },
            format='json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("bloqueada", response.data["message"])
