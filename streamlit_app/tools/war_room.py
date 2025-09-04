"""
Milkbox AI — War Room
CI status panel for Repo Doctor / Smoke / Repo Health / Repo Steward / CodeQL.

- If GITHUB_TOKEN is set, uses the GitHub REST API for precise conclusions/timestamps.
- Otherwise falls back to reading public badge SVGs and parsing "passing"/"failing".
- Click "Refresh" to clear cache and re-pull.

Run standalone:
    python -m streamlit run streamlit_app/tools/war_room.py
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Dict

import requests
import streamlit as st

# --- Repo constants
OWNER = "swanepoelchristo"
REPO = "milkbox-ai"
WORKFLOWS = {
    "Repo Doctor": "repo_doctor.yml",
    "Smoke (Imports)": "smoke.yml",
    "Repo Health": "health.yml",
    "Repo Steward": "repo_steward.yml",
    "CodeQL": "codeql.yml",
}
WORKFLOW_ORDER = list(WORKFLOWS.keys())


# ------------------------- Model -------------------------

@dataclass
class CiStatus:
    name: str
    conclusion: str          # success | failure | neutral | cancelled | timed_out | action_required | stale | queued | in_progress | unknown
    updated_at: Optional[str]
    url: Optional[str]
    source: str              # "api" or "badge"


# ------------------------- Helpers -------------------------

def _env_token() -> Optional[str]:
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    return tok.strip() if tok else None


def _api_headers(token: Optional[str]) -> Dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _badge_url(owner: str, repo: str, wf_file: str) -> str:
    return f"https://github.com/{owner}/{repo}/actions/workflows/{wf_file}/badge.svg"


def _badge_conclusion(svg_text: str) -> str:
    txt = (svg_text or "").lower()
    if "passing" in txt or "pass" in txt:
        return "success"
    if "failing" in txt or "fail" in txt:
        return "failure"
    return "unknown"


def _status_emoji(conclusion: str) -> str:
    return {
        "success": "✅",
        "failure": "❌",
        "cancelled": "⚪",
        "timed_out": "⏱️",
        "action_required": "⚠️",
        "stale": "🟡",
        "queued": "⏳",
        "in_progress": "🔵",
        "neutral": "⚪",
        "unknown": "❔",
    }.get(conclusion, "❔")


@st.cache_data(ttl=60, show_spinner=False)
def fetch_api_statuses(owner: str, repo: str, token: Optional[str]) -> Dict[str, CiStatus]:
    """Fetch latest workflow run status via GitHub API; return {} if not available."""
    headers = _api_headers(token)
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs?per_page=100"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return {}
        runs = (resp.json() or {}).get("workflow_runs", [])
    except Exception:
        return {}

    # pick the newest run per workflow file
    latest_by_wf: Dict[str, dict] = {}
    for run in runs:
        wf_path = (run.get("path") or "").split("/")[-1]
        if not wf_path:
            continue
        prev = latest_by_wf.get(wf_path)
        if not prev or (run.get("updated_at") or "") >= (prev.get("updated_at") or ""):
            latest_by_wf[wf_path] = run

    out: Dict[str, CiStatus] = {}
    for name, wf_file in WORKFLOWS.items():
        run = latest_by_wf.get(wf_file)
        if not run:
            continue
        conclusion = run.get("conclusion") or run.get("status") or "unknown"
        if conclusion == "completed" and run.get("conclusion"):
            conclusion = run["conclusion"]
        out[name] = CiStatus(
            name=name,
            conclusion=conclusion or "unknown",
            updated_at=run.get("updated_at"),
            url=run.get("html_url"),
            source="api",
        )
    return out


@st.cache_data(ttl=60, show_spinner=False)
def fetch_badge_status(owner: str, repo: str, wf_file: str) -> CiStatus:
    url = _badge_url(owner, repo, wf_file)
    conclusion = "unknown"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            conclusion = _badge_conclusion(r.text)
    except Exception:
        pass
    return CiStatus(
        name=wf_file,
        conclusion=conclusion,
        updated_at=None,
        url=f"https://github.com/{owner}/{repo}/actions/workflows/{wf_file}",
        source="badge",
    )


def _merge_api_badges(api_statuses: Dict[str, CiStatus]) -> Dict[str, CiStatus]:
    merged: Dict[str, CiStatus] = {}
    for name in WORKFLOW_ORDER:
        wf = WORKFLOWS[name]
        merged[name] = api_statuses.get(name) or CiStatus(
            name=name,
            conclusion=fetch_badge_status(OWNER, REPO, wf).conclusion,
            updated_at=None,
            url=f"https://github.com/{OWNER}/{REPO}/actions/workflows/{wf}",
            source="badge" if name not in api_statuses else "api",
        )
    return merged


def _issues_link() -> str:
    return f"https://github.com/{OWNER}/{REPO}/issues"


def _actions_link() -> str:
    return f"https://github.com/{OWNER}/{REPO}/actions"


# ------------------------- UI -------------------------

def _status_bar(statuses: Dict[str, CiStatus]) -> None:
    cols = st.columns(len(WORKFLOW_ORDER))
    for i, name in enumerate(WORKFLOW_ORDER):
        st_status = statuses.get(name)
        with cols[i]:
            if not st_status:
                st.metric(label=name, value="❔ unknown")
                continue
            emoji = _status_emoji(st_status.conclusion)
            st.metric(label=name, value=f"{emoji} {st_status.conclusion}")
            if st_status.url:
                st.caption(f"[open run]({st_status.url}) · via {st_status.source}")


def render() -> None:
    """Entrypoint for Streamlit (and for Smoke contract)."""
    st.set_page_config(page_title="War Room · Milkbox AI", page_icon="🛠️", layout="wide")

    st.title("🛠️ War Room")
    st.caption("CI overview for Repo Doctor · Smoke · Repo Health · Repo Steward · CodeQL")

    left, mid, right = st.columns([1, 1, 3])
    with left:
        if st.button("🔄 Refresh", help="Clear cache and refresh", use_container_width=True):
            fetch_api_statuses.clear()
            fetch_badge_status.clear()
            st.experimental_rerun()
    with mid:
        st.link_button("🧪 Open Actions", _actions_link(), use_container_width=True)
    with right:
        st.link_button("🐞 Open Issues", _issues_link(), use_container_width=True)

    st.divider()

    token = _env_token()
    if token:
        st.info("Using GitHub API (token detected) for precise status and timestamps.", icon="🔑")
    else:
        st.warning(
            "No GITHUB_TOKEN detected. Falling back to badge parsing (less precise). "
            "Set GITHUB_TOKEN for richer details.",
            icon="ℹ️",
        )

    api = fetch_api_statuses(OWNER, REPO, token)
    statuses = _merge_api_badges(api)

    _status_bar(statuses)

    with st.expander("Details"):
        st.json({
            n: {
                "conclusion": s.conclusion,
                "updated_at": s.updated_at,
                "url": s.url,
                "source": s.source,
            } for n, s in statuses.items()
        })

    st.caption("Tip: export a personal access token as GITHUB_TOKEN for more accurate reporting.")


if __name__ == "__main__":
    render()

