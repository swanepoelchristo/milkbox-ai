import json
from pathlib import Path
import streamlit as st

STATE = Path("standards") / "reg_state.json"
WATCHLOG = Path("standards") / "watch_log.md"
WATCHLIST = Path("standards") / "watchlist.yaml"

# GitHub UI links (adjust owner/repo if your repo name changes)
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "swanepoelchristo/milkbox-ai")
GITHUB_BASE = f"https://github.com/{GITHUB_REPO}"
ACTIONS_DISPATCH = f"{GITHUB_BASE}/actions/workflows/reg_watch.yml"
WATCHLIST_URL = f"{GITHUB_BASE}/blob/main/standards/watchlist.yaml"
LOG_URL = f"{GITHUB_BASE}/blob/main/standards/watch_log.md"


def _pill(label: str):
    st.markdown(
        f"<span style='display:inline-block;padding:2px 8px;border-radius:8px;"
        f"background:#111318;border:1px solid #2a2d35;font-size:12px;'>{label}</span>",
        unsafe_allow_html=True,
    )


def render_reg_watch(title: str = "🔎 Regulatory Watch") -> None:
    st.subheader(title)

    st.caption(
        "This reads the daily/triggered checks from "
        "`standards/watch_log.md` and the current state in `standards/reg_state.json`. "
        "The GitHub Action **Regulatory Watch** is scheduled and can also be run on demand."
    )

    cols = st.columns([1, 1, 2])
    with cols[0]:
        if st.button("▶️ Run now", help="Open the workflow to manually dispatch a run"):
            st.experimental_set_query_params()  # no-op but keeps UI responsive
            st.markdown(f"[Open workflow dispatch]({ACTIONS_DISPATCH})")

    with cols[1]:
        if st.button("📝 Edit watchlist.yaml"):
            st.markdown(f"[Open watchlist.yaml]({WATCHLIST_URL})")

    with cols[2]:
        st.write("**Secrets supported (optional):** ", end="")
        for key in ("DOC_ISO22000_URL", "DOC_HACCP_URL", "DOC_LOCAL_REG_URL", "DOC_SOP_INDEX_URL"):
            st.write(" ", end="")
            _pill(key)

    with st.expander("📌 Current state (`reg_state.json`)", expanded=False):
        if STATE.exists():
            try:
                data = json.loads(STATE.read_text(encoding="utf-8"))
                st.json(data)
            except Exception as e:
                st.error(f"Could not parse reg_state.json: {e}")
        else:
            st.info("No `reg_state.json` yet. Trigger the Action once, then refresh.")

    st.subheader("📑 Latest watch log")
    if WATCHLOG.exists():
        # Render md but avoid huge scroll — cap height a bit
        st.markdown(
            f"<div style='max-height:360px;overflow:auto;border:1px solid #2a2d35;"
            f"border-radius:8px;padding:8px;'>"
            f"{WATCHLOG.read_text(encoding='utf-8')}"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"[Open full log in GitHub]({LOG_URL})")
    else:
        st.info("No `watch_log.md` yet. Trigger the Action once, then refresh.")

    st.caption(
        "Tip: set repo **secrets** for protected URLs, or put public URLs directly in "
        "`standards/watchlist.yaml`. The Action will update the state and log when changes are found."
    )
