#!/usr/bin/env python
"""把 OpenAPI 契约 diff 回写到 PR 评论（幂等更新，错误不影响构建结果）。"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

if __package__:
    from .github_comments import upsert_comment
else:
    from github_comments import upsert_comment

MARKER = "<!-- mctp-contract -->"
MAX_CHARS = 6000


def read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return ""


def read_status() -> str:
    return read("contract-status.txt").strip() or "unavailable"


def truncate(text: str) -> str:
    text = text.strip()
    if len(text) <= MAX_CHARS:
        return text
    return text[:MAX_CHARS] + "\n\n> 输出过长已截断，完整内容见 CI 归档产物。"


def build_comment(breaking: str, changelog: str, status: str, build_url: str) -> str:
    has_breaking = status == "1"
    lines = [MARKER, "### API 契约变更", ""]
    if has_breaking:
        lines.append("*检测到破坏性变更，需要前端确认；GitHub Actions 可用 PR 标签 `allow-breaking` 放行。*")
    elif status == "0":
        lines.append("未检测到破坏性变更。")
    else:
        lines.append("契约检查未完成或执行失败；不能确认兼容性，请查看 CI 日志。")
    lines.append("")
    details = truncate(breaking) if has_breaking else truncate(changelog)
    if details:
        lines.extend(["<details><summary>变更详情</summary>", "", "```markdown", details, "```", "", "</details>"])
    else:
        lines.append("_没有可展示的 diff 输出。_")
    if build_url:
        lines.extend(["", f"[查看 CI 构建]({build_url})"])
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
        if response.status == 204:
            return None
        return json.loads(response.read().decode())


def main() -> None:
    token = os.environ.get("GH_TOKEN")
    repo = os.environ.get("GH_REPO")
    pull_request = os.environ.get("PR_NUMBER")
    if not token or not repo or not pull_request:
        print("缺少 GH_TOKEN / GH_REPO / PR_NUMBER，跳过契约评论")
        return
    body = build_comment(
        read("contract-breaking.md"),
        read("contract-changelog.md"),
        read_status(),
        os.environ.get("BUILD_URL", ""),
    )
    action, comment_id, duplicates = upsert_comment(repo, pull_request, token, body, MARKER, github)
    if action == "updated":
        print(f"已更新 PR #{pull_request} 的契约评论 #{comment_id}（清理 {duplicates} 条重复）")
    else:
        print(f"已新增 PR #{pull_request} 的契约评论 #{comment_id}")


if __name__ == "__main__":
    try:
        main()
    except (urllib.error.URLError, OSError, KeyError, ValueError) as error:
        print(f"契约评论失败（不影响构建结果）：{error}")
        raise SystemExit(1) from error
