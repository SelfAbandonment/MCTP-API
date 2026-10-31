#!/usr/bin/env python
"""把测试与覆盖率结果回写到 PR 评论（幂等更新，错误不影响构建结果）。"""

from __future__ import annotations

import glob
import json
import os
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

MARKER = "<!-- mctp-ci-report -->"


def collect_tests() -> dict[str, int]:
    totals = {"tests": 0, "failed": 0, "skipped": 0}
    for path in glob.glob("TEST-*.xml"):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        totals["tests"] += len(root.findall(".//testcase"))
        totals["failed"] += len(root.findall(".//failure")) + len(root.findall(".//error"))
        totals["skipped"] += len(root.findall(".//skipped"))
    return totals


def collect_coverage() -> str:
    try:
        root = ET.parse("coverage.xml").getroot()
        rate = float(root.attrib.get("line-rate", "0"))
    except (OSError, ET.ParseError, ValueError):
        return ""
    return f"{rate * 100:.1f}% lines"


def build_comment(tests: dict[str, int], coverage: str, build_url: str) -> str:
    lines = [MARKER, "### CI 报告", ""]
    if tests["tests"]:
        lines.append(f"- **测试**：{tests['tests']} 通过 / {tests['failed']} 失败 / {tests['skipped']} 跳过")
    if coverage:
        lines.append(f"- **覆盖率**：{coverage}")
    if len(lines) == 3:
        lines.append("- 本次构建没有可汇总的报告")
    if build_url:
        lines.extend(["", f"[查看 Jenkins 构建]({build_url})"])
    return "\n".join(lines)


def github(path: str, method: str, token: str, payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "mctp-jenkins",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode())


def main() -> None:
    token = os.environ.get("GH_TOKEN")
    repo = os.environ.get("GH_REPO")
    pull_request = os.environ.get("PR_NUMBER")
    if not token or not repo or not pull_request:
        print("缺少 GH_TOKEN / GH_REPO / PR_NUMBER，跳过 PR 评论")
        return
    body = build_comment(collect_tests(), collect_coverage(), os.environ.get("BUILD_URL", ""))
    comments = github(f"/repos/{repo}/issues/{pull_request}/comments?per_page=100", "GET", token)
    existing = next((item for item in comments if MARKER in (item.get("body") or "")), None)
    if existing:
        github(f"/repos/{repo}/issues/comments/{existing['id']}", "PATCH", token, {"body": body})
        print(f"已更新 PR #{pull_request} 的 CI 评论 #{existing['id']}")
    else:
        created = github(f"/repos/{repo}/issues/{pull_request}/comments", "POST", token, {"body": body})
        print(f"已新增 PR #{pull_request} 的 CI 评论 #{created['id']}")


if __name__ == "__main__":
    try:
        main()
    except (urllib.error.URLError, OSError, KeyError, ValueError) as error:
        print(f"PR 评论失败（不影响构建结果）：{error}")
