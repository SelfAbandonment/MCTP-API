#!/usr/bin/env python3
"""把 Jenkins 构建结果推给 AstrBot 插件；凭证缺失或网络失败时只记录，不阻断构建。"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import datetime
from typing import Any

PLUGIN = "astrbot_plugin_mctp_ci"
DEFAULT_PATH = f"/api/v1/plugins/extensions/{PLUGIN}/webhook"
STATUSES = {"failure", "success", "warning", "fixed", "info"}


def _trim(value: Any) -> str:
    return str(value or "").strip()


def build_payload(env: dict[str, str] | None = None) -> dict[str, Any]:
    env = env or os.environ
    status = _trim(env.get("NOTIFY_STATUS")).lower()
    if status not in STATUSES:
        status = "info"
    details = [item.strip() for item in _trim(env.get("NOTIFY_DETAILS")).split("|") if item.strip()]
    return {
        "base": _trim(env.get("ASTRBOT_BASE_URL")).rstrip("/"),
        "api_key": _trim(env.get("ASTRBOT_API_KEY")),
        "token": _trim(env.get("ASTRBOT_WEBHOOK_TOKEN")),
        "path": _trim(env.get("ASTRBOT_WEBHOOK_PATH")) or DEFAULT_PATH,
        "payload": {
            "repo": _trim(env.get("NOTIFY_REPO")) or "MCTP-API",
            "event": _trim(env.get("NOTIFY_EVENT")) or "ci",
            "status": status,
            "title": _trim(env.get("NOTIFY_TITLE")) or "MCTP-API 构建通知",
            "subtitle": _trim(env.get("NOTIFY_SUBTITLE")),
            "branch": _trim(env.get("NOTIFY_BRANCH")),
            "pr": _trim(env.get("NOTIFY_PR")),
            "actor": _trim(env.get("NOTIFY_ACTOR")),
            "commit": _trim(env.get("NOTIFY_COMMIT")),
            "duration": _trim(env.get("NOTIFY_DURATION")),
            "details": details,
            "url": _trim(env.get("NOTIFY_URL")),
            "time": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M"),
        },
    }


def send_notification(
    env: dict[str, str] | None = None,
    opener: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    config = build_payload(env)
    missing = [
        name
        for name, value in (
            ("ASTRBOT_BASE_URL", config["base"]),
            ("ASTRBOT_API_KEY", config["api_key"]),
            ("ASTRBOT_WEBHOOK_TOKEN", config["token"]),
        )
        if not value
    ]
    if missing:
        return {"skipped": True, "reason": f"缺少 {', '.join(missing)}"}

    data = json.dumps(config["payload"], ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{config['base']}{config['path']}",
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}",
            "X-CI-Token": config["token"],
        },
    )
    opener = opener or urllib.request.urlopen
    with opener(request, timeout=15) as response:
        body = response.read(300).decode("utf-8", "replace")
        status = getattr(response, "status", 200)
    return {"skipped": False, "status": status, "body": body}


def main() -> int:
    try:
        result = send_notification()
        if result.get("skipped"):
            print(f"AstrBot 通知跳过：{result['reason']}")
        else:
            print(f"AstrBot 通知已发送：HTTP {result['status']} {result['body']}")
        return 0
    except urllib.error.HTTPError as exc:
        print(f"AstrBot 通知失败（不影响构建）：HTTP {exc.code} {exc.reason}")
        return 1
    except Exception as exc:  # noqa: BLE001 - 通知不能影响构建
        print(f"AstrBot 通知失败（不影响构建）：{exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
