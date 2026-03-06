"""ShowDoc documentation sync script.

Reads markdown files from docs/showdoc/ based on the manifest (docs/showdoc.txt),
computes MD5 hashes for incremental sync, and pushes changes to ShowDoc API.

Usage:
    python scripts/sync_showdoc.py            # Incremental sync (only changed files)
    python scripts/sync_showdoc.py --force     # Force sync all documents
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_FILE = PROJECT_ROOT / "docs" / "showdoc.txt"
DOCS_DIR = PROJECT_ROOT / "docs" / "showdoc"
CACHE_FILE = PROJECT_ROOT / ".showdoc_cache.json"

# ---------------------------------------------------------------------------
# Load environment variables from .env
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass  # python-dotenv not installed; fall back to system env vars

SHOWDOC_URL = os.getenv("SHOWDOC_URL", "").rstrip("/")
SHOWDOC_API_KEY = os.getenv("SHOWDOC_API_KEY", "")
SHOWDOC_API_TOKEN = os.getenv("SHOWDOC_API_TOKEN", "")


def _check_env() -> None:
    """Validate that all required environment variables are set."""
    missing = []
    if not SHOWDOC_URL:
        missing.append("SHOWDOC_URL")
    if not SHOWDOC_API_KEY:
        missing.append("SHOWDOC_API_KEY")
    if not SHOWDOC_API_TOKEN:
        missing.append("SHOWDOC_API_TOKEN")
    if missing:
        print(f"[ERROR] Missing environment variables: {', '.join(missing)}")
        print("  -> Please set them in .env or export them in your shell.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Hash cache helpers
# ---------------------------------------------------------------------------
def _load_cache() -> dict[str, str]:
    """Load the hash cache from disk."""
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_cache(cache: dict[str, str]) -> None:
    """Persist the hash cache to disk."""
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def _md5(content: str) -> str:
    """Return the MD5 hex digest of a string."""
    return hashlib.md5(content.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Manifest parsing
# ---------------------------------------------------------------------------
def _parse_manifest() -> list[dict]:
    """Parse docs/showdoc.txt and return a list of document descriptors.

    Each line format:  分类 | 标题 | 相对文件路径
    Lines starting with '#' or blank lines are skipped.
    """
    if not MANIFEST_FILE.exists():
        print(f"[ERROR] Manifest file not found: {MANIFEST_FILE}")
        sys.exit(1)

    entries: list[dict] = []
    for lineno, raw in enumerate(MANIFEST_FILE.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3:
            print(f"  [WARN] Skipping malformed line {lineno}: {raw}")
            continue
        cat, title, rel_path = parts
        filepath = PROJECT_ROOT / rel_path
        if not filepath.exists():
            print(f"  [WARN] File not found (line {lineno}): {filepath}")
            continue
        entries.append({"cat": cat, "title": title, "path": filepath, "rel": rel_path})
    return entries


# ---------------------------------------------------------------------------
# ShowDoc API
# ---------------------------------------------------------------------------
def _push_page(cat_name: str, page_title: str, page_content: str, order: int) -> bool:
    """Push a single page to ShowDoc. Returns True on success."""
    url = f"{SHOWDOC_URL}/server/index.php?s=/api/item/updateByApi"
    data = urlencode(
        {
            "api_key": SHOWDOC_API_KEY,
            "api_token": SHOWDOC_API_TOKEN,
            "cat_name": cat_name,
            "page_title": page_title,
            "page_content": page_content,
            "s_number": order,
        }
    ).encode("utf-8")

    req = Request(url, data=data, method="POST")
    try:
        with urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            if body.get("error_code") == 0:
                return True
            print(f"    API error: {body.get('error_message', body)}")
            return False
    except (HTTPError, URLError, OSError) as exc:
        print(f"    Network error: {exc}")
        return False


# ---------------------------------------------------------------------------
# Main sync logic
# ---------------------------------------------------------------------------
def sync(force: bool = False) -> None:
    """Run the sync process."""
    _check_env()
    entries = _parse_manifest()
    if not entries:
        print("[WARN] No documents found in manifest.")
        return

    cache = _load_cache()
    total = len(entries)
    synced = 0
    skipped = 0
    failed = 0
    failed_list: list[str] = []

    print(f"ShowDoc Sync  target={SHOWDOC_URL}")
    print(f"  Documents: {total}  Mode: {'FORCE' if force else 'incremental'}")
    print("-" * 50)

    for idx, entry in enumerate(entries, 1):
        content = entry["path"].read_text(encoding="utf-8")
        content_hash = _md5(content)
        cache_key = entry["rel"]

        if not force and cache.get(cache_key) == content_hash:
            skipped += 1
            print(f"  [{idx}/{total}] SKIP  {entry['cat']} / {entry['title']}")
            continue

        print(f"  [{idx}/{total}] SYNC  {entry['cat']} / {entry['title']} ...", end=" ")
        ok = _push_page(entry["cat"], entry["title"], content, idx)
        if ok:
            synced += 1
            cache[cache_key] = content_hash
            print("OK")
        else:
            failed += 1
            failed_list.append(f"{entry['cat']} / {entry['title']}")
            print("FAIL")

    _save_cache(cache)

    print("-" * 50)
    print(f"  Done!  synced={synced}  skipped={skipped}  failed={failed}")
    if failed_list:
        print("  Failed documents:")
        for name in failed_list:
            print(f"    - {name}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Sync documentation to ShowDoc")
    parser.add_argument("--force", action="store_true", help="Force sync all documents (ignore cache)")
    args = parser.parse_args()
    sync(force=args.force)


if __name__ == "__main__":
    main()
