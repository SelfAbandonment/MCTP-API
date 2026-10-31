import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.notify_astrbot import build_payload, send_notification  # noqa: E402, I001


ENV = {
    "ASTRBOT_BASE_URL": "http://127.0.0.1:6185/",
    "ASTRBOT_API_KEY": "abk_test",
    "ASTRBOT_WEBHOOK_TOKEN": "hook-token",
    "NOTIFY_REPO": "MCTP-API",
    "NOTIFY_EVENT": "ci",
    "NOTIFY_STATUS": "failure",
    "NOTIFY_TITLE": "构建失败",
    "NOTIFY_BRANCH": "feat/x",
    "NOTIFY_DETAILS": "ruff 通过 | 契约检查失败 | ",
}


class BuildPayloadTest(unittest.TestCase):
    def test_maps_env_and_trims(self):
        config = build_payload(ENV)
        self.assertEqual(config["base"], "http://127.0.0.1:6185")
        self.assertEqual(
            config["path"],
            "/api/v1/plugins/extensions/astrbot_plugin_mctp_ci/webhook",
        )
        self.assertEqual(config["payload"]["status"], "failure")
        self.assertEqual(config["payload"]["details"], ["ruff 通过", "契约检查失败"])

    def test_defaults(self):
        config = build_payload({"NOTIFY_TITLE": "hello", "NOTIFY_STATUS": "boom"})
        self.assertEqual(config["payload"]["status"], "info")
        self.assertEqual(config["payload"]["repo"], "MCTP-API")


class SendNotificationTest(unittest.TestCase):
    def test_skips_without_config(self):
        result = send_notification({})
        self.assertTrue(result["skipped"])
        self.assertIn("ASTRBOT_BASE_URL", result["reason"])

    def test_posts_json_with_headers(self):
        captured = {}

        class FakeResponse:
            status = 200

            def read(self, _limit):
                return b'{"ok":true,"sent":1}'

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        def opener(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse()

        result = send_notification(ENV, opener=opener)
        self.assertFalse(result["skipped"])
        self.assertEqual(result["status"], 200)
        request = captured["request"]
        self.assertTrue(request.full_url.endswith("/astrbot_plugin_mctp_ci/webhook"))
        self.assertEqual(request.get_header("Authorization"), "Bearer abk_test")
        self.assertEqual(request.get_header("X-ci-token"), "hook-token")
        self.assertEqual(captured["timeout"], 5)


if __name__ == "__main__":
    unittest.main()
