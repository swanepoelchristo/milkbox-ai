# streamlit_app/tools/food_safety.py
# Milky Roads AI — Food Safety dashboard (with Regulatory Watch card)

from __future__ import annotations
import os
import json
from pathlib import Path
from datetime import datetime
import streamlit as st

APP_ROOT = Path(__file__).resolve().parents[2]  # repo root
STANDARDS_DIR = APP_ROOT / "standards"
WATCH_LOG = STANDARDS_DIR / "watch_log.md"
STATE_JSON = STANDARDS_DIR / ".reg_state.json"
WATCHLIST = APP_ROOT / "standards" / "watchlist.yaml"

# Best-effort repo slug for links, can be overridden by secrets
# e.g. "swanepoelchristo/milkbox-ai"
REPO_SLUG = (
    st.secrets.get("GITHUB_REPO", "")
    or os.getenv("GITHUB_REPO", "")
    or "swanepoelchristo/milkbox-ai"  # <— fallback; harmless if it’s yours
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


def _nice_ts(ts: str | int | float | None) -> str:
    try:
        if isinstance(ts, (int, float)):
            return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M UTC")
        if isinstance(ts, str):
            # try ISO first
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M UTC")
            except Exception:
                return ts
    except Exception:
        pass
    return "—"


def render() -> None:
    st.header("Milky Roads AI — Food Safety")

    # --- Quick links / placeholders (simple, non-persistent operators' inputs) ---
    with st.expander("📄 Quick access — Documents & SOPs", expanded=False):
        st.caption("Paste links for fast access (no storage yet; permanent links belong in **standards/watchlist.yaml** or Streamlit **Secrets**).")
        c1, c2 = st.columns(2)
        with c1:
            iso = st.text_input("ISO 22000 URL", placeholder="https://...")
            haccp = st.text_input("Codex HACCP URL", placeholder="https://...")
        with c2:
            local = st.text_input("Local/Regulation URL", placeholder="https://...")
            sop = st.text_input("Company SOP Index URL", placeholder="https://...")
        st.write("Open:")
        cols = st.columns(4)
        if iso: cols[0].link_button("ISO 22000", iso)
        if haccp: cols[1].link_button("HACCP", haccp)
        if local: cols[2].link_button("Local Reg", local)
        if sop: cols[3].link_button("SOP Index", sop)

    # --- Regulatory Watch card ---
    st.markdown("### 🔎 Regulatory Watch")
    st.caption(
        "This reads the daily/triggered checks from **standards/watch_log.md** and the current "
        "state in **standards/.reg_state.json**. The GitHub Action *Regulatory Watch* is "
        "scheduled and can also be run on demand."
    )

    # Summary row
    cols = st.columns([1, 1, 2])
    with cols[0]:
        st.link_button("▶️ Run now", ACTIONS_URL, help="Open the GitHub Action to trigger a check")
    with cols[1]:
        st.link_button("🗂️ Edit watchlist.yaml", WATCHLIST_URL, help="Open your watchlist to add/update documents")
    with cols[2]:
        st.write(
            "Secrets supported (optional): `DOC_ISO22000_URL`, `DOC_HACCP_URL`, "
            "`DOC_LOCAL_REG_URL`, `DOC_SOP_INDEX_URL`."
        )

    # Current state
    state = _read_json(STATE_JSON)
    with st.expander("📌 Current state (.reg_state.json)", expanded=False):
        if not state:
            st.info("No state found yet. After the first Action run, this will show ETag/Last-Modified/Length for each document.")
        else:
            st.json(state)

    # Watch log
    st.markdown("#### 🧾 Latest watch log")
    if WATCH_LOG.exists():
        # Show just the last N lines for readability
        raw = _read_text(WATCH_LOG, "")
        if raw:
            lines = raw.strip().splitlines()
            last = "\n".join(lines[-120:])  # last ~120 lines
            st.markdown(last or "_(empty log)_")
        else:
            st.info("Log is empty.")
    else:
        st.info("No watch_log.md yet. Trigger the Action once, then refresh.")

    # Footer / hints
    st.caption(
        "Tip: set your repository secrets for protected URLs, or put public URLs directly in "
        "`standards/watchlist.yaml`. The Action will update the state & log and commit changes."
    )
import streamlit as st

# shared UI components
try:
    from components.reg_watch import render_reg_watch
except Exception:  # fail-safe if path changes
    def render_reg_watch(*_, **__):
        st.warning("Regulatory Watch component missing. Ensure `components/reg_watch.py` exists.")

try:
    from components.quick_links import render_quick_links_docs
except Exception:
    def render_quick_links_docs():
        st.warning("Quick Links component missing. Ensure `components/quick_links.py` exists.")


def render():
    st.title("Milky Roads AI — Food Safety")

    # 1) Quick access to key docs & SOP index
    render_quick_links_docs()

    # 2) Your domain UI could go here (temperature logs, CCP checks, uploaders, etc)
    #    We keep the structure but don't enforce any data yet—no crashes.
    st.markdown("### Temperature Logs")
    st.info(
        "Drop your existing log UI here. If you had previous code, paste it above this call. "
        "This placeholder ensures the page renders even when no data source is configured."
    )

    # 3) Shared Regulatory Watch card
    st.divider()
    render_reg_watch("🔎 Regulatory Watch")
