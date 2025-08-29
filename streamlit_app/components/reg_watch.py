# streamlit_app/components/reg_watch.py
# Shared "Regulatory Watch" card for all tools

from __future__ import annotations
import os
import json
from pathlib import Path
from datetime import datetime
import streamlit as st

# Resolve repo root from this file's location:
# components/  -> streamlit_app/ -> repo root
APP_ROOT = Path(__file__).resolve().parents[2]
STANDARDS_DIR = APP_ROOT / "standards"
WATCH_LOG = STANDARDS_DIR / "watch_log.md"
STATE_JSON = STANDARDS_DIR / ".reg_state.json"

# Repo slug to build Action + file links (prefer secrets/env; fall back to example)
REPO_SLUG = (
    st.secrets.get("GITHUB_REPO", "")
    or os.getenv("GITHUB_REPO", "")
    or "swanepoelchristo/milkbox-ai"  # harmless fallback; change if you like
)

ACTIONS_URL = f"https://github.com/{REPO_SLUG}/actions/workflows/reg-watch.yml"
WATCHLIST_URL = f"https://github.com/{REPO_SLUG}/blob/main/standards/watchlist.yaml"


def _read_text(path: Path, fallback: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return fallback


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def render_reg_watch(title: str = "🔎 Regulatory Watch") -> None:
    """Render the Regulatory Watch card (links + current state + latest log)."""
    st.markdown(f"### {title}")
    st.caption(
        "Daily/triggered checks for your standards watchlist. "
        "Data comes from **standards/.reg_state.json** and **standards/watch_log.md**."
    )

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.link_button("▶️ Run now", ACTIONS_URL, help="Open GitHub Actions to manually trigger a check")
    with c2:
        st.link_button("🗂️ Edit watchlist.yaml", WATCHLIST_URL, help="Open the watchlist in GitHub")
    with c3:
        st.write(
            "Secrets supported: `DOC_ISO22000_URL`, `DOC_HACCP_URL`, "
            "`DOC_LOCAL_REG_URL`, `DOC_SOP_INDEX_URL`."
        )

    state = _read_json(STATE_JSON)
    with st.expander("📌 Current state (.reg_state.json)", expanded=False):
        if not state:
            st.info("No state yet. After the first Action run, this will show ETag/Last-Modified/Length per document.")
        else:
            st.json(state)

    st.markdown("#### 🧾 Latest watch log")
    if WATCH_LOG.exists():
        raw = _read_text(WATCH_LOG, "")
        if raw:
            # Tail for readability
            lines = raw.strip().splitlines()
            st.markdown("\n".join(lines[-120:]) or "_(empty log)_")
        else:
            st.info("Log is empty.")
    else:
        st.info("No watch_log.md found yet. Trigger the Action once, then refresh.")
