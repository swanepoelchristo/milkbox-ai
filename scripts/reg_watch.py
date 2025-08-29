#!/usr/bin/env python3
"""
Regulatory Watcher
- Reads standards/watchlist.yaml
- Resolves each document's URL from (1) GitHub Secret name, (2) inline url field, or (3) standards/urls/<key>.txt
- Fetches remote HEAD metadata (ETag, Last-Modified, Content-Length, final URL)
- Compares against previous snapshot in standards/.reg_state.json
- If changes are detected:
    * updates standards/.reg_state.json
    * appends an entry into standards/watch_log.md
    * returns exit code 0 (workflow will commit the changes)
"""

from __future__ import annotations
import os
import sys
import json
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

import requests
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]         # repo root
WATCHLIST = ROOT / "standards" / "watchlist.yaml"
STATE_FILE = ROOT / "standards" / ".reg_state.json"
URLS_DIR = ROOT / "standards" / "urls"
LOG_MD = ROOT / "standards" / "watch_log.md"

HEADERS = {
    "User-Agent": "Milkbox-AI-RegWatch/1.0 (+https://github.com/)",
    "Accept": "*/*",
}

TIMEOUT = 20


@dataclass
class Doc:
    key: str
    name: str
    secret: Optional[str] = None
    url: Optional[str] = None


def load_watchlist() -> List[Doc]:
    if not WATCHLIST.exists():
        print(f"ERROR: watchlist not found: {WATCHLIST}", file=sys.stderr)
        sys.exit(1)

    y = yaml.safe_load(WATCHLIST.read_text(encoding="utf-8")) or {}
    docs = []
    for item in (y.get("docs") or []):
        key = item.get("key")
        name = item.get("name", key)
        secret = item.get("secret") or None
        url = item.get("url") or None
        if not key:
            print("WARNING: skipping item without 'key'", file=sys.stderr)
            continue
        docs.append(Doc(key=key, name=name, secret=secret, url=url))
    return docs


def resolve_url(doc: Doc) -> Optional[str]:
    # 1) From secret
    if doc.secret:
        env_val = os.getenv(doc.secret)
        if env_val:
            return env_val.strip()

    # 2) From inline url
    if doc.url:
        return doc.url.strip()

    # 3) From fallback file standards/urls/<key>.txt
    fallback = URLS_DIR / f"{doc.key}.txt"
    if fallback.exists():
        return fallback.read_text(encoding="utf-8").strip()

    return None


def head_metadata(url: str) -> Dict[str, Any]:
    """
    Try HEAD first; if blocked, fall back to GET with minimal range.
    """
    s = requests.Session()
    s.headers.update(HEADERS)

    try:
        r = s.head(url, allow_redirects=True, timeout=TIMEOUT)
    except requests.RequestException as e:
        # Fall back to a tiny GET
        try:
            r = s.get(url, headers={"Range": "bytes=0-0", **HEADERS}, allow_redirects=True, timeout=TIMEOUT, stream=True)
        except requests.RequestException as e2:
            return {"ok": False, "error": f"{type(e2).__name__}: {e2}"}
    final_url = str(r.url)

    etag = r.headers.get("ETag", "")
    last_mod = r.headers.get("Last-Modified", "")
    clen = r.headers.get("Content-Length", "")
    # Some servers don’t return content-length on HEAD; keep blank in that case

    # Build a signature that changes if the resource changes
    signature = f"status={r.status_code}|url={final_url}|etag={etag}|last={last_mod}|len={clen}"
    return {
        "ok": True,
        "status": r.status_code,
        "final_url": final_url,
        "etag": etag,
        "last_modified": last_mod,
        "content_length": clen,
        "signature": signature,
        "checked_at": int(time.time()),
    }


def load_state() -> Dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_state(state: Dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def append_log(changes: List[Dict[str, Any]]) -> None:
    LOG_MD.parent.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%d %H:%M:%S %Z", time.gmtime())
    lines = []
    lines.append(f"## {ts}")
    for ch in changes:
        name = ch['name']
        url = ch['meta'].get('final_url') or ch['url']
        old_sig = ch.get("old_signature", "(none)")
        new_sig = ch['meta'].get('signature', '')
        lines.append(f"- **{name}** changed → {url}")
        lines.append(f"  - old: `{old_sig}`")
        lines.append(f"  - new: `{new_sig}`")
    lines.append("")  # trailing newline
    with LOG_MD.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> int:
    docs = load_watchlist()
    state = load_state()
    updated = []
    errors = []

    for doc in docs:
        url = resolve_url(doc)
        if not url:
            errors.append((doc.name, "No URL resolved (secret/url/fallback missing)"))
            continue

        meta = head_metadata(url)
        if not meta.get("ok"):
            errors.append((doc.name, meta.get("error", "unknown error")))
            continue

        prev_sig = ((state.get(doc.key) or {}).get("signature")) if state else None
        new_sig = meta["signature"]
        if new_sig != prev_sig:
            updated.append({
                "key": doc.key,
                "name": doc.name,
                "url": url,
                "old_signature": prev_sig,
                "meta": meta
            })
            state[doc.key] = {
                "name": doc.name,
                "url": url,
                **meta
            }

    # Write state and log if anything changed
    if updated:
        print(f"Detected {len(updated)} change(s). Updating state + log...")
        save_state(state)
        append_log(updated)
    else:
        print("No changes detected.")

    if errors:
        print("\nNon-fatal issues:")
        for name, err in errors:
            print(f" - {name}: {err}")

    # Always exit 0 so the workflow can commit log/state when changed.
    return 0


if __name__ == "__main__":
    sys.exit(main())
