"""
Milkbox AI — War Room
CI status panel for Repo Doctor / Smoke / Repo Health / Repo Steward / CodeQL.

- If GITHUB_TOKEN is set, uses the GitHub REST API for precise conclusions/timestamps.
- Otherwise falls back to reading public badge SVGs and parsing "passing"/"failing".
- Click "Refresh" to clear cache and re-pull.

Safe to run standalone:
    streamlit run streamlit_app/tools/war_room.py
"""

from __future__ import annotations

import os
import time
import json
from dataclasses import dataclass
from typing import Optional, Dict, Tuple, List

import requests
import streamlit as st

# --- typo guard in case older code used `ma(...)` by mistake
ma = max  # noqa: F401

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

WORKFLOW_ORDER = list(WORKFLOWS.keys())  # Display order in the panel


# ------------------------- Helpers -------------------------


@dataclass
class CiStatus:
    name: str
    conclusion: str  # success | failure | neutral | cancelled | timed_out | action_required | stale | queued | in_progress | unknown
    updated_at: Optional[str]
    url: Optional[str]
    source: str  # "api" or "badge"


def _env_token() -> Optional[str]:
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    return tok.strip() if tok else None


def _api_headers(token: Optional[str]) -> Dict[str, str]:
    hdrs = {"Accept": "application/vnd.github+json"}
    if token:
        hdrs["Authorization"] = f"Bearer {token}"
    return hdrs


def _badge_url(owner: str, repo: str, wf_file: str) -> str:
    # Public badge SVG
    return f"https://github.com/{owner}/{repo}/actions/workflows/{wf_file}/badge.svg"


def _badge_conclusion(svg_text: str) -> str:
    # Very light parsing: GitHub badges include text "passing" or "failing"
    txt = svg_text.lower()
    if "passing" in txt or "pass" in txt:
        return "success"
    if "failing" in txt or "fail" in txt:
        return "failure"
    # Degenerate fallback
    return "unknown"


def _status_color(conclusion: str) -> str:
    mapping = {
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
    }
    return mapping.get(conclusion, "❔")


@st.cache_data(ttl=60, show_spinner=False)
def fetch_api_statuses(owner: str, repo: str, token: Optional[str]) -> Dict[str, CiStatus]:
    """
    Get latest workflow run conclusions via GitHub API.
    Falls back to badges if API returns non-200.
    """
    statuses: Dict[str, CiStatus] = {}
    headers = _api_headers(token)

    # List workflow runs (we’ll filter by workflow filename)
    # API doc: GET /repos/{owner}/{repo}/actions/runs
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs?per_page=100"
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        # API blocked or unauthenticated — fall back entirely to badges
        return {}

    runs = resp.json().get("workflow_runs", [])
    # Build best/latest run per workflow file
    latest_by_wf: Dict[str, Dict] = {}
    for run in runs:
        wf_path = (run.get("path") or "").split("/")[-1]  # ".github/workflows/xxx.yml" -> "xxx.yml"
        if wf_path:
            prev = latest_by_wf.get(wf_path)
            # choose latest by updated_at
            prev_ts = (prev or {}).get("updated_at") or ""
            cur_ts = run.get("updated_at") or ""
            if cur_ts >= prev_ts:
                latest_by_wf[wf_path] = run

    for name, wf_file in WORKFLOWS.items():
        run = latest_by_wf.get(wf_file)
        if not run:
            continue
        conclusion = run.get("conclusion") or run.get("status") or "unknown"
        # Normalize some statuses
        if conclusion == "completed" and run.get("conclusion"):
            conclusion = run.get("conclusion")
        updated = run.get("updated_at")
        html_url = run.get("html_url")
        statuses[name] = CiStatus(
            name=name,
            conclusion=conclusion or "unknown",
            updated_at=updated,
            url=html_url,
            source="api",
        )
    return statuses


@st.cache_data(ttl=60, show_spinner=False)
def fetch_badge_status(owner: str, repo: str, wf_file: str) -> CiStatus:
    url = _badge_url(owner, repo, wf_file)
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            conclusion = _badge_conclusion(r.text)
        else:
            conclusion = "unknown"
    except Exception:
        conclusion = "unknown"
    return CiStatus(
        name=wf_file,
        conclusion=conclusion,
        updated_at=None,
        url=f"https://github.com/{owner}/{repo}/actions/workflows/{wf_file}",
        source="badge",
    )


def _merge_api_badges(api_statuses: Dict[str, CiStatus]) -> Dict[str, CiStatus]:
    """
    Ensure every workflow has a status.
    Use API where present; badge fallback otherwise.
    """
    merged: Dict[str, CiStatus] = {}
    for name in WORKFLOW_ORDER:
        wf = WORKFLOWS[name]
        if name in api_statuses:
            merged[name] = api_statuses[name]
        else:
            b = fetch_badge_status(OWNER, REPO, wf)
            merged[name] = CiStatus(
                name=name,
                conclusion=b.conclusion,
                updated_at=None,
                url=b.url,
                source="badge",
            )
    return merged


def _status_bar(statuses: Dict[str, CiStatus]) -> None:
    cols = st.columns(len(WORKFLOW_ORDER))
    for idx, name in enumerate(WORKFLOW_ORDER):
        col = cols[idx]
        st_status = statuses.get(name)
        if not st_status:
            with col:
                st.metric(label=name, value="❔ unknown")
            continue
        icon = _status_color(st_status.conclusion)
        label = f"{icon} {st_status.conclusion}"
        with col:
            st.metric(label=name, value=label)
            if st_status.url:
                st.caption(f"[open run]({st_status.url}) · via {st_status.source}")


def _issues_link() -> str:
    return f"https://github.com/{OWNER}/{REPO}/issues"


def _actions_link() -> str:
    return f"https://github.com/{OWNER}/{REPO}/actions"


# ------------------------- UI -------------------------


def render() -> None:
    """Entrypoint for Streamlit (and for Smoke contract)."""
    st.set_page_config(page_title="War Room · Milkbox AI", page_icon="🛠️", layout="wide")

    st.title("🛠️ War Room")
    st.caption("CI overview for Repo Doctor · Smoke · Repo Health · Repo Steward · CodeQL")

    # Controls
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

    # Fetch statuses (API preferred; fallback to badges for any WF missing)
    api_statuses = fetch_api_statuses(OWNER, REPO, token)
    statuses = _merge_api_badges(api_statuses)

    # Status pills
    _status_bar(statuses)

    # Raw details (expandable)
    with st.expander("Details"):
        as_dict = {
            name: {
                "conclusion": s.conclusion,
                "updated_at": s.updated_at,
                "url": s.url,
                "source": s.source,
            }
            for name, s in statuses.items()
        }
        st.json(as_dict)

    st.caption("Tip: export a personal access token as GITHUB_TOKEN for more accurate reporting.")


# Allow standalone execution
if __name__ == "__main__":
    render()
