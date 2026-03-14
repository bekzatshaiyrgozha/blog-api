from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse

User = get_user_model()

class UserLanguageTimezoneTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="u@example.com", password="pass1234", first_name="A", last_name="B")
        self.client = APIClient()
        # Получить JWT или использовать force_authenticate depending on your auth
        self.client.force_authenticate(user=self.user)

    def test_patch_language_valid(self):
        url = reverse("update-language")
        resp = self.client.patch(url, {"language": "ru"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.language, "ru")

    def test_patch_timezone_invalid(self):
        url = reverse("update-timezone")
        resp = self.client.patch(url, {"timezone": "No/SuchZone"}, format="json")
        self.assertEqual(resp.status_code, 400)