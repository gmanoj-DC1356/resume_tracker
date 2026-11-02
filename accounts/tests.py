from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class AccountsPingTests(TestCase):
    def test_ping_requires_authentication(self):
        res = APIClient().get("/api/v1/auth/ping/")
        self.assertIn(res.status_code, (401, 403))

    def test_ping_ok_when_authenticated(self):
        user = get_user_model().objects.create_user("tester", password="x-unused-test-pw-1")
        client = APIClient()
        client.force_authenticate(user)
        self.assertEqual(client.get("/api/v1/auth/ping/").status_code, 200)
