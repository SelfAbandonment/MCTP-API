"""
认证模块测试
"""

from allauth.socialaccount.models import SocialAccount
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


class ChangePasswordTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="password-user",
            email="password@example.com",
            password="OldStrongPass123!",
        )
        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_change_password_blacklists_existing_refresh_token(self):
        response = self.client.post(
            "/api/v1/auth/password/",
            {
                "old_password": "OldStrongPass123!",
                "new_password": "NewStrongPass123!",
                "new_password_confirm": "NewStrongPass123!",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token_response = self.client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": self.refresh_token},
        )
        self.assertEqual(token_response.status_code, status.HTTP_401_UNAUTHORIZED)


class SessionBridgeTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="session-user",
            email="session@example.com",
            password="StrongPass123!",
        )

    def test_session_token_requires_authentication(self):
        response = self.client.post("/api/v1/auth/token/session/")

        # SessionAuthentication reports an unauthenticated request as 403.
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_session_token_returns_jwt_pair_and_user(self):
        self.client.force_login(self.user)

        response = self.client.post("/api/v1/auth/token/session/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], 200)
        data = response.data["data"]
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertEqual(data["user"]["username"], "session-user")
        # The returned refresh token must be usable by the existing JWT API.
        refresh = self.client.post("/api/v1/auth/token/refresh/", {"refresh": data["refresh"]})
        self.assertEqual(refresh.status_code, status.HTTP_200_OK)

    def test_allauth_headless_password_login_then_exchange(self):
        # allauth headless browser client: login with the regular account.
        response = self.client.post(
            "/_allauth/browser/v1/auth/login",
            {"username": "session-user", "password": "StrongPass123!"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["meta"]["is_authenticated"])

        exchange = self.client.post("/api/v1/auth/token/session/")
        self.assertEqual(exchange.status_code, status.HTTP_200_OK)
        self.assertIn("access", exchange.data["data"])

    def test_headless_config_is_public(self):
        response = self.client.get("/_allauth/browser/v1/config")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.json())


class MicrosoftUnbindTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="bound-user", password="StrongPass123!")
        SocialAccount.objects.create(
            user=self.user,
            provider="microsoft",
            uid="0123456789abcdef0123456789abcdef",
            extra_data={"mc_uuid": "0123456789abcdef0123456789abcdef", "mc_username": "Steve"},
        )
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_unbind_removes_social_account(self):
        response = self.client.delete("/api/v1/auth/microsoft/unbind/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(SocialAccount.objects.filter(user=self.user, provider="microsoft").exists())

    def test_unbind_without_binding_returns_404(self):
        SocialAccount.objects.filter(user=self.user).delete()

        response = self.client.delete("/api/v1/auth/microsoft/unbind/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MicrosoftProviderTests(APITestCase):
    def test_provider_registered_with_minecraft_uid(self):
        from types import SimpleNamespace

        from allauth.socialaccount import providers

        provider = providers.registry.get_class("microsoft")
        self.assertIsNotNone(provider)
        self.assertEqual(provider.id, "microsoft")
        # Provider instances require an allauth app; a minimal stand-in is
        # enough to exercise the pure extraction helpers.
        app = SimpleNamespace(pk=None, provider="microsoft", settings={}, client_id="client", secret="secret")
        instance = provider(SimpleNamespace(), app=app)
        self.assertEqual(instance.extract_uid({"mc_uuid": "abc"}), "abc")
        self.assertEqual(instance.get_default_scope(), ["XboxLive.signin", "offline_access"])

    def test_provider_callback_url_is_allauth_callback(self):
        from django.urls import reverse

        self.assertEqual(
            reverse("microsoft_callback"),
            "/accounts/microsoft/login/callback/",
        )
