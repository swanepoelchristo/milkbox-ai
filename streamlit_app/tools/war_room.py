"""
Milkbox AI — War Room
CI status panel for Repo Doctor / Smoke / Repo Health / Repo Steward / CodeQL.

- If GITHUB_TOKEN is set, uses the GitHub REST API for precise conclusions/timestamps.
- Otherwise falls back to reading public badge SVGs and parsing "passing"/"failing".
- Click "Refresh" to re-pull; use "Hard refresh" to also clear Streamlit cache.

Run standalone:
    python -m streamlit run streamlit_app/tools/war_room.py
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
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
    }.get((conclusion or "unknown").lower(), "❔")

def _age_text(iso_ts: Optional[str]) -> str:
    if not iso_ts:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        sec = max(0, (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds())
        if sec < 60:
            return f"{int(sec)}s ago"
        if sec < 3600:
            return f"{int(sec // 60)}m ago"
        if sec < 86400:
            return f"{int(sec // 3600)}h ago"
        return f"{int(sec // 86400)}d ago"
    except Exception:
        return iso_ts

def _mode_chip(api_mode: bool) -> str:
    """Small pill to show whether we're using API mode or Badge mode."""
    txt = "API mode" if api_mode else "Badge mode"
    bg  = "#16a34a" if api_mode else "#f59e0b"    # green / amber
    icon = "🔑 " if api_mode else "🛈 "
    return f"""
    <span style="
      display:inline-block;margin-left:.5rem;
      background:{bg};color:#fff;border-radius:999px;
      padding:3px 10px;font-weight:600;font-size:.85rem;">
      {icon}{txt}
    </span>
    """

# ------------------------- Data -------------------------

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

    # newest run per workflow file
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
        conclusion = (run.get("conclusion") or run.get("status") or "unknown").lower()
        if conclusion == "completed" and run.get("conclusion"):
            conclusion = run.get("conclusion", "unknown").lower()
        out[name] = CiStatus(
            name=name,
            conclusion=conclusion,
            updated_at=run.get("updated_at") or run.get("run_started_at"),
            url=run.get("html_url"),
            source="api",
        )
    return out

@st.cache_data(ttl=60, show_spinner=False)
def fetch_badge_status(owner: str, repo: str, wf_file: str) -> CiStatus:
    # tiny retry for flaky network
    url = _badge_url(owner, repo, wf_file)
    conclusion = "unknown"
    for _ in range(2):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                conclusion = _badge_conclusion(r.text)
                break
        except Exception:
            time.sleep(0.2)
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
        if name in api_statuses:
            merged[name] = api_statuses[name]
        else:
            badge = fetch_badge_status(OWNER, REPO, wf)
            merged[name] = CiStatus(
                name=name,
                conclusion=badge.conclusion,
                updated_at=None,
                url=badge.url,
                source="badge",
            )
    return merged

def _issues_link() -> str:
    return f"https://github.com/{OWNER}/{REPO}/issues"

def _actions_link() -> str:
    return f"https://github.com/{OWNER}/{REPO}/actions"

# ------------------------- UI -------------------------

def _status_bar(statuses: Dict[str, CiStatus]) -> None:
    n = max(1, len(WORKFLOW_ORDER))  # guard: never zero columns
    cols = st.columns(n)
    for i, name in enumerate(WORKFLOW_ORDER):
        st_status = statuses.get(name)
        with cols[min(i, n - 1)]:
            if not st_status:
                st.metric(label=name, value="❔ unknown")
                continue
            emoji = _status_emoji(st_status.conclusion)
            age = _age_text(st_status.updated_at)
            st.metric(label=name, value=f"{emoji} {st_status.conclusion}")
            if st_status.url:
                st.caption(f"{age} · [open run]({st_status.url}) · via {st_status.source}")

def render() -> None:
    """Entrypoint for Streamlit (and for Smoke contract)."""
    st.set_page_config(page_title="War Room · Milkbox AI", page_icon="🛠️", layout="wide")

    # Detect once and show mode chip in the title
    token = _env_token()
    api_mode = bool(token)
    st.markdown(
        f"<h1 style='display:inline'>🛠️ War Room</h1>{_mode_chip(api_mode)}",
        unsafe_allow_html=True,
    )
    st.caption("CI overview for Repo Doctor · Smoke · Repo Health · Repo Steward · CodeQL")

    left, mid, right = st.columns([1, 1, 3])
    with left:
        if st.button("🔄 Refresh", help="Re-pull without clearing cache", use_container_width=True):
            st.rerun()
    with mid:
        if st.button("♻️ Hard refresh", help="Clear Streamlit cache then reload", use_container_width=True):
            fetch_api_statuses.clear()
            fetch_badge_status.clear()
            st.rerun()
    with right:
        st.link_button("🧪 Open Actions", _actions_link(), use_container_width=True)

    st.link_button("🐞 Open Issues", _issues_link(), use_container_width=True)

    st.divider()

    if api_mode:
        st.info("Using GitHub API (token detected) for precise status and timestamps.", icon="🔑")
    else:
        st.warning(
            "No GITHUB_TOKEN detected. Falling back to badge parsing (less precise). "
            "Set GITHUB_TOKEN for richer details.",
            icon="ℹ️",
        )

    api = fetch_api_statuses(OWNER, REPO, token if api_mode else None)
    statuses = _merge_api_badges(api)

    _status_bar(statuses)

    with st.expander("Details"):
        st.json({
            n: {
                "conclusion": s.conclusion,
                "updated_at": s.updated_at,
                "updated_age": _age_text(s.updated_at),
                "url": s.url,
                "source": s.source,
            } for n, s in statuses.items()
        })

    st.caption("Tip: export a personal access token as GITHUB_TOKEN for more accurate reporting.")

if __name__ == "__main__":
    render()
