from datetime import timedelta

from allauth.socialaccount.models import SocialAccount
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.generators import SchemaGenerator
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from mctp_api.auth.models import MicrosoftAccount

from .models import Announcement

User = get_user_model()


class CommunityTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user("staff", is_staff=True)
        cls.player = User.objects.create_user("player", email="player@example.com")
        cls.other_staff = User.objects.create_user("other-staff", is_staff=True)
        cls.superuser = User.objects.create_user("superuser", is_superuser=True)
        cls.inactive_staff = User.objects.create_user("inactive-staff", is_staff=True, is_active=False)
        cls.account = MicrosoftAccount.objects.create(
            user=cls.player, mc_uuid="1234567890abcdef1234567890abcdef", mc_username="MinecraftPlayer"
        )
        cls.published = Announcement.objects.create(
            title="Published",
            body="Plain text <not rendered HTML>",
            is_published=True,
            published_at=timezone.now() - timedelta(days=1),
        )
        cls.draft = Announcement.objects.create(title="Draft", body="Unpublished")
        cls.future = Announcement.objects.create(
            title="Future",
            body="Scheduled",
            is_published=True,
            published_at=timezone.now() + timedelta(days=1),
        )

    def staff_login(self):
        self.client.force_authenticate(self.staff)

    def announcement_url(self, announcement=None):
        return f"/api/v1/manage/announcements/{(announcement or self.published).pk}/"

    def player_url(self, player=None):
        return f"/api/v1/manage/players/{(player or self.player).pk}/"

    def assert_envelope(self, response, code):
        self.assertEqual(response.status_code, code, response.data)
        self.assertEqual(set(response.data), {"code", "message", "data"})
        self.assertEqual(response.data["code"], code)

    def test_public_only_published_and_not_future(self):
        response = self.client.get("/api/v1/announcements/")
        self.assert_envelope(response, 200)
        self.assertEqual(response.data["data"]["count"], 1)
        item = response.data["data"]["results"][0]
        self.assertEqual(item["id"], self.published.pk)
        self.assertEqual(set(item), {"id", "title", "summary", "body", "published_at", "updated_at"})
        self.assertEqual(item["body"], self.published.body)

    def test_public_pagination_and_order(self):
        now = timezone.now()
        Announcement.objects.bulk_create(
            [Announcement(title=f"New {n}", body="Body", is_published=True, published_at=now) for n in range(21)]
        )
        response = self.client.get("/api/v1/announcements/")
        page = response.data["data"]
        self.assertEqual(page["count"], 22)
        self.assertEqual(len(page["results"]), 20)
        self.assertIsNone(page["previous"])
        self.assertIn("page=2", page["next"])
        ids = [item["id"] for item in page["results"]]
        self.assertEqual(ids, sorted(ids, reverse=True))
        page2 = self.client.get(page["next"]).data["data"]
        self.assertEqual(len(page2["results"]), 2)
        self.assertIsNone(page2["next"])
        self.assertIsNotNone(page2["previous"])
        self.assert_envelope(self.client.get("/api/v1/announcements/?page=999"), 404)

    def test_management_permissions_all_operations(self):
        operations = [
            ("get", "/api/v1/manage/announcements/", None),
            ("post", "/api/v1/manage/announcements/", {"title": "X", "body": "Y"}),
            ("get", self.announcement_url(), None),
            ("patch", self.announcement_url(), {"title": "Changed"}),
            ("delete", self.announcement_url(), None),
            ("get", "/api/v1/manage/players/", None),
            ("get", self.player_url(), None),
            ("patch", self.player_url(), {"is_active": False}),
        ]
        for user, expected in [(None, 401), (self.player, 403), (self.inactive_staff, 403)]:
            self.client.force_authenticate(user=user)
            for method, url, payload in operations:
                with self.subTest(user=user, method=method, url=url):
                    response = getattr(self.client, method)(url, payload, format="json")
                    self.assert_envelope(response, expected)
        self.published.refresh_from_db()
        self.assertEqual(self.published.title, "Published")
        self.player.refresh_from_db()
        self.assertTrue(self.player.is_active)

    def test_announcement_crud_and_publish_default(self):
        self.staff_login()
        response = self.client.post(
            "/api/v1/manage/announcements/",
            {"title": "New", "body": "Text", "is_published": True},
            format="json",
        )
        self.assert_envelope(response, 201)
        created = Announcement.objects.get(pk=response.data["data"]["id"])
        self.assertIsNotNone(created.published_at)
        self.assertEqual(created.summary, "")
        url = self.announcement_url(created)
        self.assert_envelope(self.client.get(url), 200)
        response = self.client.patch(url, {"title": "Updated", "summary": "Short", "body": "Changed"}, format="json")
        self.assert_envelope(response, 200)
        self.assertEqual(response.data["data"]["title"], "Updated")
        self.assertEqual(response.data["data"]["published_at"], created.published_at.isoformat().replace("+00:00", "Z"))
        self.assert_envelope(self.client.delete(url), 200)
        self.assertFalse(Announcement.objects.filter(pk=created.pk).exists())
        self.assert_envelope(self.client.get(url), 404)

    def test_draft_and_scheduling_transitions(self):
        self.staff_login()
        url = self.announcement_url(self.draft)
        response = self.client.patch(url, {"is_published": True, "published_at": None}, format="json")
        self.assertIsNotNone(response.data["data"]["published_at"])
        future = timezone.now() + timedelta(days=2)
        response = self.client.patch(url, {"published_at": future.isoformat()}, format="json")
        self.assert_envelope(response, 200)
        self.assertEqual(self.client.get("/api/v1/announcements/").data["data"]["count"], 1)
        response = self.client.patch(url, {"is_published": False, "published_at": None}, format="json")
        self.assertIsNone(response.data["data"]["published_at"])
        response = self.client.patch(url, {"is_published": True}, format="json")
        self.assertIsNotNone(response.data["data"]["published_at"])
        self.assertEqual(self.client.get("/api/v1/announcements/").data["data"]["count"], 2)

    def test_announcement_validation_and_unknown_fields(self):
        self.staff_login()
        invalid_payloads = [
            {},
            {"title": "", "body": "Text"},
            {"title": "X" * 161, "body": "Text"},
            {"title": "X", "body": ""},
            {"title": "X", "body": "Y", "summary": "X" * 241},
            {"title": "X", "body": "Y", "is_published": None},
            {"title": "X", "body": "Y", "published_at": "bad-date"},
            {"title": "X", "body": "Y", "unknown": "value"},
            {"title": "X", "body": "Y", "id": 999},
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                self.assert_envelope(self.client.post("/api/v1/manage/announcements/", payload, format="json"), 400)
        self.assert_envelope(
            self.client.patch(self.announcement_url(), {"created_at": timezone.now().isoformat()}, format="json"), 400
        )
        self.assertEqual(Announcement.objects.count(), 3)

    def test_management_list_contains_drafts_and_future_with_pagination(self):
        self.staff_login()
        Announcement.objects.bulk_create([Announcement(title=f"Draft {n}", body="Body") for n in range(21)])
        response = self.client.get("/api/v1/manage/announcements/")
        self.assert_envelope(response, 200)
        self.assertEqual(response.data["data"]["count"], 24)
        self.assertEqual(len(response.data["data"]["results"]), 20)
        self.assertIn("is_published", response.data["data"]["results"][0])
        page2 = self.client.get(response.data["data"]["next"]).data["data"]
        self.assertEqual(len(page2["results"]), 4)
        self.assertEqual(self.client.get(self.announcement_url(self.draft)).status_code, 200)
        self.assertEqual(self.client.get(self.announcement_url(self.future)).status_code, 200)

    def test_player_search_and_shape(self):
        self.staff_login()
        expected_fields = {
            "id",
            "username",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
            "minecraft",
        }
        for search in ["PLAYER", "player@example.com", "MinecraftPlayer", self.account.mc_uuid]:
            with self.subTest(search=search):
                response = self.client.get("/api/v1/manage/players/", {"search": search})
                self.assert_envelope(response, 200)
                self.assertEqual(response.data["data"]["count"], 1)
                item = response.data["data"]["results"][0]
                self.assertEqual(set(item), expected_fields)
                self.assertEqual(
                    item["minecraft"], {"uuid": self.account.mc_uuid, "username": self.account.mc_username}
                )
        response = self.client.get(self.player_url(self.other_staff))
        self.assertIsNone(response.data["data"]["minecraft"])
        self.assertEqual(self.client.get("/api/v1/manage/players/?search=absent").data["data"]["count"], 0)

    def test_player_pagination(self):
        self.staff_login()
        User.objects.bulk_create([User(username=f"new-player-{n}") for n in range(21)])
        response = self.client.get("/api/v1/manage/players/?search=new-player")
        self.assertEqual(response.data["data"]["count"], 21)
        self.assertEqual(len(response.data["data"]["results"]), 20)
        self.assertIn("search=new-player", response.data["data"]["next"])
        self.assertEqual(len(self.client.get(response.data["data"]["next"]).data["data"]["results"]), 1)

    def test_staff_can_disable_and_reactivate_regular_player(self):
        self.staff_login()
        for active in [False, True]:
            response = self.client.patch(self.player_url(), {"is_active": active}, format="json")
            self.assert_envelope(response, 200)
            self.assertEqual(response.data["data"]["is_active"], active)
            self.player.refresh_from_db()
            self.assertEqual(self.player.is_active, active)
            self.assertEqual(self.player.username, "player")
            self.assertFalse(self.player.is_staff)

    def test_protected_accounts_cannot_be_mutated(self):
        self.staff_login()
        for player in [self.staff, self.other_staff, self.superuser, self.inactive_staff]:
            with self.subTest(player=player.username):
                self.assert_envelope(
                    self.client.patch(self.player_url(player), {"is_active": not player.is_active}, format="json"), 403
                )
                old_active = player.is_active
                player.refresh_from_db()
                self.assertEqual(player.is_active, old_active)

    def test_player_only_active_is_writable_and_required(self):
        self.staff_login()
        for field in ["is_staff", "is_superuser", "username", "email", "id", "password", "minecraft", "unknown"]:
            with self.subTest(field=field):
                response = self.client.patch(self.player_url(), {"is_active": False, field: True}, format="json")
                self.assert_envelope(response, 400)
        for payload in [{}, {"is_active": None}, {"is_active": "invalid"}, []]:
            self.assert_envelope(self.client.patch(self.player_url(), payload, format="json"), 400)
        self.player.refresh_from_db()
        self.assertTrue(self.player.is_active)

    def test_unsupported_methods_and_missing_players(self):
        self.staff_login()
        self.assert_envelope(self.client.delete(self.player_url()), 405)
        self.assert_envelope(self.client.put(self.player_url(), {"is_active": False}, format="json"), 405)
        self.assert_envelope(self.client.post("/api/v1/manage/players/", {}, format="json"), 405)
        self.assert_envelope(self.client.put(self.announcement_url(), {}, format="json"), 405)
        self.assert_envelope(self.client.get("/api/v1/manage/players/999999/"), 404)
        self.assert_envelope(
            self.client.patch("/api/v1/manage/players/999999/", {"is_active": False}, format="json"), 404
        )

    def test_disabled_players_token_no_longer_authenticates(self):
        token = str(AccessToken.for_user(self.player))
        self.staff_login()
        self.client.patch(self.player_url(), {"is_active": False}, format="json")
        self.client.force_authenticate(user=None)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assert_envelope(self.client.get("/api/v1/auth/me/"), 401)

    def test_me_exposes_flags_but_put_does_not_allow_privilege_escalation(self):
        self.client.force_authenticate(self.player)
        response = self.client.get("/api/v1/auth/me/")
        for field, value in [("is_staff", False), ("is_superuser", False), ("is_active", True)]:
            self.assertIs(response.data["data"][field], value)
        response = self.client.put(
            "/api/v1/auth/me/",
            {
                "username": "renamed",
                "is_staff": True,
                "is_superuser": True,
                "is_active": False,
            },
            format="json",
        )
        self.assert_envelope(response, 200)
        self.player.refresh_from_db()
        self.assertEqual(self.player.username, "renamed")
        self.assertFalse(self.player.is_staff)
        self.assertFalse(self.player.is_superuser)
        self.assertTrue(self.player.is_active)

    def test_announcement_registered_in_admin(self):
        self.assertIn(Announcement, admin.site._registry)

    def test_list_schemas_match_single_enveloped_pagination(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        components = schema["components"]["schemas"]
        for path, name in [
            ("/api/v1/announcements/", "PublicAnnouncement"),
            ("/api/v1/manage/announcements/", "Announcement"),
            ("/api/v1/manage/players/", "Player"),
        ]:
            response_schema = schema["paths"][path]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
            self.assertEqual(response_schema, {"$ref": f"#/components/schemas/{name}ListResponse"})
            self.assertEqual(set(components[f"{name}ListResponse"]["properties"]), {"code", "message", "data"})
            page = components[f"{name}Page"]["properties"]
            self.assertEqual(set(page), {"results", "count", "next", "previous"})
            self.assertEqual(page["results"]["type"], "array")


class PublicAnnouncementDetailTests(APITestCase):
    """公开详情、公开搜索与社区概览（v1 增量接口）。"""

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user("staff", is_staff=True)
        cls.player = User.objects.create_user("player", email="player@example.com")
        cls.inactive = User.objects.create_user("inactive", is_active=False)
        cls.legacy_bound = User.objects.create_user("legacy-bound")
        cls.social_bound = User.objects.create_user("social-bound")
        MicrosoftAccount.objects.create(user=cls.legacy_bound, mc_uuid="1" * 32, mc_username="LegacyBound")
        SocialAccount.objects.create(
            user=cls.social_bound,
            provider="microsoft",
            uid="2" * 32,
            extra_data={"mc_uuid": "2" * 32, "mc_username": "SocialBound"},
        )
        cls.published = Announcement.objects.create(
            title="开服公告",
            summary="本周更新说明",
            body="服务器将在周六维护。",
            is_published=True,
            published_at=timezone.now() - timedelta(hours=2),
        )
        cls.draft = Announcement.objects.create(title="草稿公告", body="未发布")
        cls.future = Announcement.objects.create(
            title="预告公告",
            body="明天见",
            is_published=True,
            published_at=timezone.now() + timedelta(days=1),
        )

    def assert_envelope(self, response, code):
        self.assertEqual(response.status_code, code, response.data)
        self.assertEqual(set(response.data), {"code", "message", "data"})
        self.assertEqual(response.data["code"], code)

    def test_detail_returns_published_announcement_without_auth(self):
        response = self.client.get(f"/api/v1/announcements/{self.published.pk}/")
        self.assert_envelope(response, 200)
        self.assertEqual(
            set(response.data["data"]),
            {"id", "title", "summary", "body", "published_at", "updated_at"},
        )
        self.assertEqual(response.data["data"]["id"], self.published.pk)
        self.assertEqual(response.data["data"]["body"], self.published.body)

    def test_detail_hides_drafts_scheduled_and_missing_announcements(self):
        for pk in [self.draft.pk, self.future.pk, self.published.pk + 999_999]:
            with self.subTest(pk=pk):
                self.assert_envelope(self.client.get(f"/api/v1/announcements/{pk}/"), 404)

    def test_detail_ignores_stale_bearer_tokens(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-token")
        self.assert_envelope(self.client.get(f"/api/v1/announcements/{self.published.pk}/"), 200)

    def test_public_search_covers_title_summary_and_body(self):
        for term, expected_title in [
            ("开服", "开服公告"),
            ("本周更新", "开服公告"),
            ("维护", "开服公告"),
            ("草稿", None),
            ("公告", "开服公告"),
        ]:
            with self.subTest(term=term):
                response = self.client.get("/api/v1/announcements/", {"search": term})
                self.assert_envelope(response, 200)
                results = response.data["data"]["results"]
                titles = [item["title"] for item in results]
                if expected_title is None:
                    self.assertEqual(titles, [])
                else:
                    self.assertIn(expected_title, titles)
        absent = self.client.get("/api/v1/announcements/", {"search": "不存在的关键词"})
        self.assertEqual(absent.data["data"]["count"], 0)

    def test_overview_requires_authentication(self):
        self.assert_envelope(self.client.get("/api/v1/overview/"), 401)

    def test_overview_counts_players_and_published_announcements(self):
        self.client.force_authenticate(self.player)
        response = self.client.get("/api/v1/overview/")
        self.assert_envelope(response, 200)
        data = response.data["data"]
        self.assertEqual(set(data), {"announcements", "players", "generated_at"})
        self.assertEqual(data["announcements"]["published"], 1)
        self.assertEqual(
            data["announcements"]["latest_published_at"],
            self.published.published_at.isoformat().replace("+00:00", "Z"),
        )
        self.assertEqual(data["players"], {"total": 5, "active": 4, "minecraft_bound": 2})
        self.assertTrue(data["generated_at"])

    def test_overview_latest_published_at_is_null_without_public_announcements(self):
        Announcement.objects.update(is_published=False)
        self.client.force_authenticate(self.player)
        data = self.client.get("/api/v1/overview/").data["data"]
        self.assertEqual(data["announcements"], {"published": 0, "latest_published_at": None})


class PlayerBindingTests(APITestCase):
    """玩家管理必须同时识别 allauth（新）与 MicrosoftAccount（旧）绑定。"""

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user("staff", is_staff=True)
        cls.social_player = User.objects.create_user("social-player", email="social@example.com")
        cls.legacy_player = User.objects.create_user("legacy-player", email="legacy@example.com")
        cls.plain_player = User.objects.create_user("plain-player")
        cls.social_uid = "2" * 32
        SocialAccount.objects.create(
            user=cls.social_player,
            provider="microsoft",
            uid=cls.social_uid,
            extra_data={"mc_uuid": cls.social_uid, "mc_username": "SocialMiner"},
        )
        MicrosoftAccount.objects.create(user=cls.legacy_player, mc_uuid="1" * 32, mc_username="LegacyMiner")

    def setUp(self):
        self.client.force_authenticate(self.staff)

    def test_management_list_and_detail_expose_allauth_binding(self):
        response = self.client.get("/api/v1/manage/players/", {"search": "social-player"})
        self.assertEqual(response.data["data"]["count"], 1)
        listed = response.data["data"]["results"][0]
        self.assertEqual(listed["minecraft"], {"uuid": self.social_uid, "username": "SocialMiner"})

        detail = self.client.get(f"/api/v1/manage/players/{self.social_player.pk}/")
        self.assertEqual(detail.data["data"]["minecraft"], listed["minecraft"])

    def test_management_search_matches_both_binding_flows(self):
        for term, expected_id in [
            ("SocialMiner", self.social_player.pk),
            (self.social_uid, self.social_player.pk),
            ("LegacyMiner", self.legacy_player.pk),
            ("1" * 32, self.legacy_player.pk),
        ]:
            with self.subTest(term=term):
                response = self.client.get("/api/v1/manage/players/", {"search": term})
                self.assertEqual(response.data["data"]["count"], 1)
                self.assertEqual(response.data["data"]["results"][0]["id"], expected_id)

    def test_unbound_player_has_null_minecraft(self):
        response = self.client.get(f"/api/v1/manage/players/{self.plain_player.pk}/")
        self.assertIsNone(response.data["data"]["minecraft"])

    def test_list_does_not_query_per_row(self):
        # count + page rows + one prefetch for allauth bindings.
        with self.assertNumQueries(3):
            response = self.client.get("/api/v1/manage/players/")
            self.assertEqual(response.data["data"]["count"], 4)
