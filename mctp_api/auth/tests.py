"""
认证模块测试
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class RegisterTests(APITestCase):
    def test_register_success(self):
        payload = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        response = self.client.post("/api/v1/auth/register/", payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["code"], 201)
        self.assertEqual(response.data["message"], "user registered successfully")
        self.assertEqual(response.data["data"]["username"], "testuser")
        self.assertEqual(response.data["data"]["email"], "test@example.com")
        self.assertNotIn("password", response.data["data"])
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_register_password_mismatch(self):
        payload = {
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "StrongPass123!",
            "password_confirm": "WrongPass123!",
        }
        response = self.client.post("/api/v1/auth/register/", payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], 400)
        self.assertEqual(response.data["message"], "validation error")

    def test_register_duplicate_email(self):
        User.objects.create_user(username="existing", email="dupe@example.com", password="pass123")
        payload = {
            "username": "newuser",
            "email": "dupe@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        response = self.client.post("/api/v1/auth/register/", payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], 400)

    def test_register_missing_fields(self):
        response = self.client.post("/api/v1/auth/register/", {"username": "incomplete"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password(self):
        payload = {
            "username": "weakuser",
            "email": "weak@example.com",
            "password": "123",
            "password_confirm": "123",
        }
        response = self.client.post("/api/v1/auth/register/", payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MeTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="meuser",
            email="me@example.com",
            password="StrongPass123!",
        )
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_get_me_authenticated(self):
        response = self.client.get("/api/v1/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["username"], "meuser")
        self.assertEqual(response.data["data"]["email"], "me@example.com")
        self.assertIn("id", response.data["data"])
        self.assertIn("date_joined", response.data["data"])

    def test_get_me_unauthenticated(self):
        self.client.credentials()
        response = self.client.get("/api/v1/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["message"], "authentication required")

    def test_put_me_update_username(self):
        response = self.client.put("/api/v1/auth/me/", {"username": "updated_name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["username"], "updated_name")
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "updated_name")

    def test_put_me_update_email(self):
        response = self.client.put("/api/v1/auth/me/", {"email": "new@example.com"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["email"], "new@example.com")

    def test_put_me_duplicate_email(self):
        User.objects.create_user(username="other", email="taken@example.com", password="pass123")
        response = self.client.put("/api/v1/auth/me/", {"email": "taken@example.com"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
