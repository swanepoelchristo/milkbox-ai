"""
Milkbox AI — War Room
CI status panel for Repo Doctor / Smoke / Repo Health.

- Tries GitHub API if GITHUB_TOKEN is set (better timestamps/conclusions).
- Otherwise falls back to reading public badge SVGs and parsing 'passing'/'failing'.
- Click "Refresh" to clear cache and re-pull.

Safe to run standalone:  streamlit run streamlit_app/tools/war_room.py
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Tuple

import requests
import streamlit as st

# --- Repo constants -----------------------------------------------------------

OWNER = "swanepoelchristo"
REPO = "milkbox-ai"

WORKFLOWS = {
    "Repo Doctor": "repo_doctor.yml",
    "Smoke": "smoke.yml",
    "Repo Health": "health.yml",
}

BADGES = {
    name: f"https://github.com/{OWNER}/{REPO}/actions/workflows/{wf}/badge.svg"
    for name, wf in WORKFLOWS.items()
}

ACTIONS_LINK = f"https://github.com/{OWNER}/{REPO}/actions"
TIMEOUT = (5, 15)  # connect, read


# --- Model --------------------------------------------------------------------

@dataclass
class CiStatus:
    name: str
    state: str          # success|failure|cancelled|skipped|unknown
    detail: str         # e.g., "passing" / "failing" or API conclusion
    url: str            # link to workflow runs
    last_run: Optional[str] = None


def map_conclusion_to_state(conclusion: Optional[str]) -> str:
    if not conclusion:
        return "unknown"
    c = conclusion.lower()
    if c in ("success", "passed"):
        return "success"
    if c in ("failure", "failed", "neutral", "timed_out"):
        return "failure"
    if c in ("cancelled", "stale", "action_required"):
        return "cancelled"
    if c in ("skipped",):
        return "skipped"
    return "unknown"


# --- Data fetchers (cached) ---------------------------------------------------

@st.cache_data(ttl=60)
def fetch_from_api(owner: str, repo: str, workflow_file: str) -> Optional[Tuple[str, str]]:
    """Return (conclusion, last_run_iso) using GitHub API if token present."""
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        return None
    url = (
        f"https://api.github.com/repos/{owner}/{repo}"
        f"/actions/workflows/{workflow_file}/runs?per_page=1"
    )
    r = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=TIMEOUT,
    )
    if r.status_code != 200:
        return None
    data = r.json()
    runs = data.get("workflow_runs") or []
    if not runs:
        return None
    run = runs[0]
    conclusion = run.get("conclusion") or run.get("status")
    last_run = run.get("updated_at") or run.get("created_at") or ""
    return (conclusion or "unknown", last_run)


@st.cache_data(ttl=60)
def fetch_from_badge(badge_url: str) -> Optional[str]:
    """Fetch badge SVG and return 'passing'/'failing'/etc. if detectable."""
    r = requests.get(badge_url, timeout=TIMEOUT)
    if r.status_code != 200:
        return None
    svg = r.text.lower()
    if "passing" in svg:
        return "passing"
    if "failing" in svg:
        return "failing"
    if "failure" in svg:
        return "failure"
    if "cancelled" in svg:
        return "cancelled"
    if "skipped" in svg:
        return "skipped"
    return "unknown"


def ci_status_for(name: str, wf_file: str) -> CiStatus:
    """Combine API (preferred) or badge fallback into a unified status row."""
    api = fetch_from_api(OWNER, REPO, wf_file)
    if api:
        conclusion, last_run = api
        state = map_conclusion_to_state(conclusion)
        return CiStatus(
            name=name,
            state=state,
            detail=conclusion or "unknown",
            url=f"{ACTIONS_LINK}/workflows/{wf_file}",
            last_run=last_run,
        )

    # Fallback: badge parse
    badge = fetch_from_badge(BADGES[name])
    detail = badge or "unknown"
    if detail in ("passing", "success"):
        state = "success"
    elif detail in ("failing", "failure"):
        state = "failure"
    elif detail in ("cancelled", "skipped"):
        state = detail
    else:
        state = "unknown"

    return CiStatus(
        name=name,
        state=state,
        detail=detail,
        url=f"{ACTIONS_LINK}/workflows/{wf_file}",
        last_run=None,
    )


# --- UI helpers ---------------------------------------------------------------

def pill(text: str, state: str) -> str:
    colors = {
        "success": "#16a34a",   # green-600
        "failure": "#dc2626",   # red-600
        "cancelled": "#9ca3af", # gray-400
        "skipped": "#9ca3af",
        "unknown": "#f59e0b",   # amber-500
    }
    bg = colors.get(state, "#f59e0b")
    return f"""
    <span style="
      background:{bg};
      color:white;
      padding:4px 10px;
      border-radius:999px;
      font-weight:600;
      font-size:0.85rem;">
      {text}
    </span>
    """


# --- App ----------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="Milkbox AI — War Room", page_icon="🛠️", layout="wide")

    st.title("🛠️ War Room")
    st.caption("Live CI snapshot for the Milkbox AI repository.")

    col_a, col_b = st.columns([1, 1], gap="large")

    with col_a:
        st.subheader("CI Status")
        rows = [ci_status_for(name, wf) for name, wf in WORKFLOWS.items()]
        for s in rows:
            st.markdown(
                f"**{s.name}** &nbsp; {pill(s.state.upper(), s.state)}",
                unsafe_allow_html=True,
            )
            sub = f"- Status: `{s.detail}`"
            if s.last_run:
                sub += f"  ·  Last run: `{s.last_run}`"
            sub += f"  ·  [View runs]({s.url})"
            st.markdown(sub)

        st.link_button("Open Actions", ACTIONS_LINK, use_container_width=True)

        if st.button("🔄 Refresh", use_container_width=True):
            fetch_from_api.clear()
            fetch_from_badge.clear()
            st.experimental_rerun()

    with col_b:
        st.subheader("Tips")
        st.markdown(
            """
            - Set a **`GITHUB_TOKEN`** environment variable when running locally to see exact conclusions and timestamps.
            - Branch protection on **`main`** requires Repo Doctor, Smoke, and Repo Health ✅.
            - Add new tools under `streamlit_app/tools/` and register them in `tools.yaml`.
            """
        )

    st.divider()
    st.caption("Milkbox AI · War Room · CI view")


# ----- Contract for tools loader / smoke -----
def render(*_args, **_kwargs):
    """Required entrypoint for the tools loader."""
    return main()


# --- Entrypoint for local runs ------------------------------------------------
if __name__ == "__main__":
    main()

