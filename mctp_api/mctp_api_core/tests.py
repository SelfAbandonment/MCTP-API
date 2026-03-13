from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


class HealthCheckTests(APITestCase):
    def test_public_health_endpoint_exposes_minimal_status(self):
        response = self.client.get("/api/v1/health/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], "healthy")
        self.assertIn("version", response.data["data"])
        self.assertNotIn("debug", response.data["data"])

    def test_detailed_health_endpoint_requires_authentication(self):
        response = self.client.get("/api/v1/health/detail/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["message"], "authentication required")

    def test_authenticated_user_can_view_detailed_health(self):
        user = get_user_model().objects.create_user(username="health-user", password="test-pass-123")
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/v1/health/detail/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], "healthy")
        self.assertIn("databases", response.data["data"]["components"])
        self.assertIn("application", response.data["data"]["components"])
