"""GitHub PR comment pagination and marker-based upsert helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

GitHubRequest = Callable[[str, str, str, dict | None], Any]


def upsert_comment(
    repo: str,
    pull_request: str,
    token: str,
    body: str,
    marker: str,
    github: GitHubRequest,
) -> tuple[str, int, int]:
    comments = []
    for page in range(1, 1000):
        result = github(
            f"/repos/{repo}/issues/{pull_request}/comments?per_page=100&page={page}",
            "GET",
            token,
        )
        if not isinstance(result, list):
            raise TypeError("GitHub 返回的 PR 评论列表格式无效")
        comments.extend(result)
        if len(result) < 100:
            break
    else:
        raise RuntimeError("PR 评论页数超过安全上限，无法完成幂等更新")

    matches = [item for item in comments if marker in (item.get("body") or "")]
    if matches:
        keep, *duplicates = matches
        github(
            f"/repos/{repo}/issues/comments/{keep['id']}",
            "PATCH",
            token,
            {"body": body},
        )
        for duplicate in duplicates:
            github(
                f"/repos/{repo}/issues/comments/{duplicate['id']}",
                "DELETE",
                token,
            )
        return "updated", keep["id"], len(duplicates)

    created = github(
        f"/repos/{repo}/issues/{pull_request}/comments",
        "POST",
        token,
        {"body": body},
    )
    if not isinstance(created, dict) or "id" not in created:
        raise TypeError("GitHub 未返回新建评论 ID")
    return "created", created["id"], 0
