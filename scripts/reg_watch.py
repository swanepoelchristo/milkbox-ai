#!/usr/bin/env python3
from __future__ import annotations
import os, sys, json, time
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[2]         # repo root
WATCHLIST   = ROOT / "standards" / "watchlist.yaml"
LOC_YAML    = ROOT / "standards" / "locations.yaml"
STATE_FILE  = ROOT / "standards" / "reg_state.json"
WATCH_LOG   = ROOT / "standards" / "watch_log.md"
URLS_DIR    = ROOT / "standards" / "urls"

HEADERS = {
    "User-Agent": "Milkbox-AI-RegWatch/1.1 (+https://github.com/)",
    "Accept": "*/*",
}
TIMEOUT = 20

@dataclass
class Doc:
    key: str
    name: str
    secret: Optional[str] = None
    url: Optional[str] = None

def load_yaml(p: Path) -> dict:
    if not p.exists(): return {}
    try: return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception: return {}

def load_watchlist() -> List[Doc]:
    y = load_yaml(WATCHLIST)
    docs = []
    for item in (y.get("docs") or []):
        key = item.get("key")
        name = item.get("name", key)
        secret = item.get("secret") or None
        url = item.get("url") or None
        if not key: continue
        docs.append(Doc(key=key, name=name, secret=secret, url=url))
    return docs

def resolve_url(doc: Doc) -> Optional[str]:
    # Priority: Secret → locations.yaml (by secret key) → inline url → urls/<key>.txt
    if doc.secret:
        env_val = os.getenv(doc.secret, "").strip()
        if env_val: return env_val
    locs = load_yaml(LOC_YAML)
    if doc.secret and locs.get(doc.secret):
        return (locs.get(doc.secret) or "").strip()
    if doc.url:
        return doc.url.strip()
    fb = (URLS_DIR / f"{doc.key}.txt")
    return (fb.read_text(encoding="utf-8").strip() if fb.exists() else None)

def head_metadata(url: str) -> Dict[str, Any]:
    s = requests.Session(); s.headers.update(HEADERS)
    try:
        r = s.head(url, allow_redirects=True, timeout=TIMEOUT)
    except requests.RequestException:
        try:
            r = s.get(url, headers={"Range": "bytes=0-0", **HEADERS}, allow_redirects=True, timeout=TIMEOUT, stream=True)
        except requests.RequestException as e2:
            return {"ok": False, "error": f"{type(e2).__name__}: {e2}"}
    final_url = str(r.url)
    etag = r.headers.get("ETag", "")
    last_mod = r.headers.get("Last-Modified", "")
    clen = r.headers.get("Content-Length", "")
    signature = f"status={r.status_code}|url={final_url}|etag={etag}|last={last_mod}|len={clen}"
    return {"ok": True, "status": r.status_code, "final_url": final_url, "etag": etag,
            "last_modified": last_mod, "content_length": clen, "signature": signature,
            "checked_at": int(time.time())}

def load_state() -> dict:
    if STATE_FILE.exists():
        try: return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception: pass
    return {}

def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")

def append_log(changes: List[dict]) -> None:
    WATCH_LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    lines = [f"## {ts}"]
    for ch in changes:
        name = ch['name']
        url = ch['meta'].get('final_url') or ch['url']
        old_sig = ch.get("old_signature", "(none)")
        new_sig = ch['meta'].get('signature', '')
        lines += [f"- **{name}** changed → {url}",
                  f"  - old: `{old_sig}`",
                  f"  - new: `{new_sig}`"]
    lines.append("")
    with WATCH_LOG.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main() -> int:
    docs = load_watchlist()
    state = load_state()
    updated, errors = [], []

    for doc in docs:
        url = resolve_url(doc)
        if not url:
            errors.append((doc.name, "No URL resolved (secret/locations.yaml/url/fallback missing)"))
            continue
        meta = head_metadata(url)
        if not meta.get("ok"):
            errors.append((doc.name, meta.get("error", "unknown error"))); continue
        prev_sig = ((state.get(doc.key) or {}).get("signature")) if state else None
        new_sig = meta["signature"]
        if new_sig != prev_sig:
            updated.append({"key": doc.key, "name": doc.name, "url": url, "old_signature": prev_sig, "meta": meta})
            state[doc.key] = {"name": doc.name, "url": url, **meta}

    if updated:
        print(f"Detected {len(updated)} change(s). Updating state + log…")
        save_state(state); append_log(updated)
    else:
        print("No changes detected.")

    if errors:
        print("\nNon-fatal issues:")
        for name, err in errors:
            print(f" - {name}: {err}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
