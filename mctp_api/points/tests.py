from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import PointAccount, PointGrant

User = get_user_model()


class PointsTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user("staff", email="staff@example.com", is_staff=True)
        cls.player = User.objects.create_user("player", email="player@example.com")
        cls.other = User.objects.create_user("other", email="other@example.com")
        cls.inactive = User.objects.create_user("inactive", email="inactive@example.com", is_active=False)
        cls.inactive_staff = User.objects.create_user(
            "inactive-staff", email="inactive-staff@example.com", is_staff=True, is_active=False
        )

    def grant(self, user, amount, reason="活动奖励", note="", staff=None):
        self.client.force_authenticate(staff or self.staff)
        response = self.client.post(
            "/api/v1/manage/points/grants/",
            {"user_id": user.pk, "amount": amount, "reason": reason, "note": note},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        return response

    def test_anonymous_and_player_permissions(self):
        own_urls = [
            "/api/v1/points/me/",
            "/api/v1/points/grants/",
            "/api/v1/points/leaderboard/",
        ]
        manage_urls = ["/api/v1/manage/points/"]

        self.client.force_authenticate(user=None)
        for url in own_urls + manage_urls:
            self.assertEqual(self.client.get(url).status_code, 401, url)

        self.client.force_authenticate(user=self.player)
        for url in own_urls:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        for url in manage_urls:
            self.assertEqual(self.client.get(url).status_code, 403, url)

        self.client.force_authenticate(user=None)
        response = self.client.post(
            "/api/v1/manage/points/grants/",
            {"user_id": self.player.pk, "amount": 10, "reason": "x"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_grant_accumulates_and_records_audit(self):
        self.grant(self.player, 25, note="首次发放")
        self.grant(self.player, 10, reason="二次发放")

        account = PointAccount.objects.get(user=self.player)
        self.assertEqual(account.balance, 35)
        self.assertEqual(account.total_granted, 35)
        grants = PointGrant.objects.filter(user=self.player).order_by("id")
        self.assertEqual([item.amount for item in grants], [25, 10])
        self.assertEqual([item.balance_after for item in grants], [25, 35])
        self.assertEqual(grants[0].granted_by, self.staff)
        self.assertEqual(grants[0].note, "首次发放")

    def test_grant_validation_and_missing_user(self):
        self.client.force_authenticate(self.staff)
        cases = [
            {"user_id": self.player.pk, "amount": 0, "reason": "x"},
            {"user_id": self.player.pk, "amount": -1, "reason": "x"},
            {"user_id": self.player.pk, "amount": 1_000_001, "reason": "x"},
            {"user_id": self.player.pk, "amount": 10, "reason": ""},
            {"user_id": self.player.pk, "amount": 10, "reason": "x", "unexpected": "field"},
        ]
        for payload in cases:
            response = self.client.post("/api/v1/manage/points/grants/", payload, format="json")
            self.assertEqual(response.status_code, 400, (payload, response.data))

        for user in (self.inactive, User(pk=999999)):
            response = self.client.post(
                "/api/v1/manage/points/grants/",
                {"user_id": user.pk, "amount": 10, "reason": "x"},
                format="json",
            )
            self.assertEqual(response.status_code, 404, response.data)

    def test_my_points_and_recent_grants(self):
        self.grant(self.player, 30, reason="测试")
        self.client.force_authenticate(self.player)
        response = self.client.get("/api/v1/points/me/")
        self.assertEqual(response.status_code, 200, response.data)
        data = response.data["data"]
        self.assertEqual(data["account"]["username"], "player")
        self.assertEqual(data["account"]["balance"], 30)
        self.assertEqual(data["account"]["total_granted"], 30)
        self.assertEqual(data["rank"], 1)
        self.assertEqual(len(data["recent_grants"]), 1)
        self.assertEqual(data["recent_grants"][0]["granted_by"], "staff")

    def test_my_grants_are_scoped_and_paginated(self):
        self.grant(self.player, 10)
        self.grant(self.player, 20)
        self.grant(self.other, 99)

        self.client.force_authenticate(self.player)
        response = self.client.get("/api/v1/points/grants/")
        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["results"]), 2)
        self.assertTrue(all(item["amount"] in (10, 20) for item in data["results"]))

        self.client.force_authenticate(self.other)
        response = self.client.get("/api/v1/points/grants/")
        self.assertEqual(response.data["data"]["count"], 1)
        self.assertEqual(response.data["data"]["results"][0]["amount"], 99)

    def test_leaderboard_excludes_zero_and_orders(self):
        self.grant(self.player, 50)
        self.grant(self.other, 20)

        self.client.force_authenticate(self.player)
        response = self.client.get("/api/v1/points/leaderboard/")
        self.assertEqual(response.status_code, 200)
        results = response.data["data"]["results"]
        self.assertEqual([item["username"] for item in results], ["player", "other"])
        self.assertEqual([item["rank"] for item in results], [1, 2])
        self.assertEqual(results[0]["balance"], 50)

    def test_manage_list_includes_users_without_points_and_search(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get("/api/v1/manage/points/")
        self.assertEqual(response.status_code, 200)
        usernames = [item["username"] for item in response.data["data"]["results"]]
        self.assertIn("player", usernames)
        self.assertIn("other", usernames)

        response = self.client.get("/api/v1/manage/points/?search=player")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["username"] for item in response.data["data"]["results"]], ["player"])
