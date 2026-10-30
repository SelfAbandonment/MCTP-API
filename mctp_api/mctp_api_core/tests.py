from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from mctp_api.auth.models import MicrosoftAccount


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


class OpenApiSchemaTests(APITestCase):
    def test_schema_endpoint_returns_openapi_document(self):
        response = self.client.get("/api/schema/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["openapi"], "3.0.3")
        self.assertIn("/api/v1/auth/register/", response.data["paths"])
        self.assertIn("/api/v1/auth/token/", response.data["paths"])
        self.assertIn("/api/v1/auth/token/refresh/", response.data["paths"])
        self.assertIn("/api/v1/auth/token/session/", response.data["paths"])
        self.assertIn("/api/v1/auth/microsoft/unbind/", response.data["paths"])
        self.assertIn("/api/v1/announcements/", response.data["paths"])
        self.assertIn("/api/v1/announcements/{id}/", response.data["paths"])
        self.assertIn("/api/v1/overview/", response.data["paths"])


class AdminFormTests(TestCase):
    """渲染 admin 表单，捕捉只在 change form 才暴露的 fieldsets 错误。"""

    def test_legacy_microsoft_binding_change_form_renders(self):
        model_admin = admin.site._registry[MicrosoftAccount]
        request = RequestFactory().get("/admin/")

        # Regression: fieldsets referenced mc_name/mc_id without declaring them
        # readonly, so opening any legacy row raised FieldError.
        form_class = model_admin.get_form(request)

        self.assertTrue(issubclass(form_class, forms.ModelForm))
        fields = model_admin.get_fields(request)
        self.assertIn("mc_name", fields)
        self.assertIn("mc_id", fields)
