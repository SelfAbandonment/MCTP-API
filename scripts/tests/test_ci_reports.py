import unittest
from unittest.mock import patch

from scripts import ci_report, contract_report, github_comments


class CiReportTest(unittest.TestCase):
    def test_passed_count_excludes_failures_and_skips(self):
        body = ci_report.build_comment(
            {"tests": 3, "failed": 1, "skipped": 1},
            "85.0% lines",
            "https://example.com/actions/runs/1",
        )
        self.assertIn("1 通过 / 1 失败 / 1 跳过", body)
        self.assertIn("[查看 CI 构建]", body)
        self.assertIn("85.0% lines", body)

    def test_empty_report_does_not_claim_tests_passed(self):
        body = ci_report.build_comment({"tests": 0, "failed": 0, "skipped": 0}, "", "")
        self.assertIn("没有可汇总的报告", body)
        self.assertNotIn("通过", body)


class ContractReportTest(unittest.TestCase):
    def test_missing_status_is_not_success(self):
        with patch.object(contract_report, "read", return_value=""):
            self.assertEqual(contract_report.read_status(), "unavailable")

    def test_success_reports_compatibility(self):
        body = contract_report.build_comment("", "new endpoint", "0", "")
        self.assertIn("未检测到破坏性变更", body)
        self.assertIn("new endpoint", body)

    def test_breaking_report_describes_github_label(self):
        body = contract_report.build_comment("removed endpoint", "", "1", "")
        self.assertIn("`allow-breaking`", body)
        self.assertIn("removed endpoint", body)

    def test_execution_failure_or_missing_status_is_inconclusive(self):
        for status in ("", "unavailable", "2", "125"):
            with self.subTest(status=status):
                body = contract_report.build_comment("", "", status, "")
                self.assertIn("不能确认兼容性", body)
                self.assertNotIn("未检测到破坏性变更", body)
                self.assertNotIn("标签", body)


class GitHubCommentsTest(unittest.TestCase):
    def test_upsert_searches_all_pages_and_removes_duplicates(self):
        calls = []

        def github(path, method, _token, payload=None):
            calls.append((path, method, payload))
            if method == "GET" and path.endswith("page=1"):
                return [{"id": item, "body": "<!-- other -->"} for item in range(100)]
            if method == "GET":
                return [
                    {"id": 101, "body": "<!-- marker -->"},
                    {"id": 102, "body": "<!-- marker -->"},
                ]
            return {"id": 103}

        result = github_comments.upsert_comment(
            "owner/repo",
            "12",
            "token",
            "<!-- marker --> updated",
            "<!-- marker -->",
            github,
        )

        self.assertEqual(result, ("updated", 101, 1))
        self.assertEqual([call[1] for call in calls], ["GET", "GET", "PATCH", "DELETE"])
        self.assertIn("page=2", calls[1][0])

    def test_upsert_creates_comment_only_after_all_pages(self):
        calls = []

        def github(path, method, _token, _payload=None):
            calls.append((path, method))
            if method == "GET":
                if path.endswith("page=1"):
                    return [{"id": item, "body": "other"} for item in range(100)]
                return []
            return {"id": 201}

        result = github_comments.upsert_comment(
            "owner/repo",
            "12",
            "token",
            "<!-- marker -->",
            "<!-- marker -->",
            github,
        )

        self.assertEqual(result, ("created", 201, 0))
        self.assertEqual([method for _, method in calls], ["GET", "GET", "POST"])


if __name__ == "__main__":
    unittest.main()
