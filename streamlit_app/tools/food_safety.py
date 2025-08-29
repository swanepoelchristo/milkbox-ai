import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st
import yaml

APP_ROOT = Path(__file__).resolve().parents[1]           # streamlit_app/
REPO_ROOT = APP_ROOT.parent                               # repo root
STANDARDS_DIR = REPO_ROOT / "standards"
WATCHLIST = STANDARDS_DIR / "watchlist.yaml"
REG_STATE = STANDARDS_DIR / "reg_state.json"
WATCH_LOG = STANDARDS_DIR / "watch_log.md"
DEPT_CFG = STANDARDS_DIR / "departments.yaml"

# Optional secrets for protected URLs (visible hint only in UI)
SECRETS_HINT = [
    "DOC_ISO22000_URL",
    "DOC_HACCP_URL",
    "DOC_LOCAL_REG_URL",
    "DOC_SOP_INDEX_URL",
]

# ---------- small helpers ----------

def read_yaml(p: Path) -> Optional[dict]:
    try:
        if not p.exists():
            return None
        with p.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return None

def read_text(p: Path) -> str:
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="ignore")

def read_json(p: Path) -> dict:
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def get_departments() -> List[dict]:
    data = read_yaml(DEPT_CFG) or {}
    return data.get("departments", [])

def list_sops(dir_path: Path) -> List[str]:
    if not dir_path.exists():
        return []
    files = []
    for p in dir_path.glob("**/*"):
        if p.is_file():
            rel = p.relative_to(REPO_ROOT).as_posix()
            files.append(rel)
    return sorted(files)

def has_secret(name: str) -> bool:
    try:
        return st.secrets.get(name) is not None
    except Exception:
        return False

# ---------- UI blocks ----------

def ui_quick_access():
    with st.expander("Quick access — Documents & SOPs", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("📄 **ISO 22000**")
            st.caption("Add a public URL in `watchlist.yaml` or set `DOC_ISO22000_URL` in Streamlit secrets.")
            if has_secret("DOC_ISO22000_URL"):
                st.success("Secret available: DOC_ISO22000_URL")
        with col2:
            st.write("📄 **HACCP**")
            st.caption("Add a public URL in `watchlist.yaml` or set `DOC_HACCP_URL` in Streamlit secrets.")
            if has_secret("DOC_HACCP_URL"):
                st.success("Secret available: DOC_HACCP_URL")
        with col3:
            st.write("🏛️ **Local/State Regulation**")
            st.caption("Add a public URL in `watchlist.yaml` or set `DOC_LOCAL_REG_URL` in Streamlit secrets.")
            if has_secret("DOC_LOCAL_REG_URL"):
                st.success("Secret available: DOC_LOCAL_REG_URL")

def ui_reg_watch():
    st.subheader("🔬 Regulatory Watch")
    st.caption(
        "This reads the daily/triggered checks from `standards/watch_log.md` "
        "and the current state in `standards/reg_state.json`. "
        "The GitHub Action **Regulatory Watch** runs on a schedule and can also be run on demand."
    )
    cols = st.columns([1, 1, 3])
    with cols[0]:
        st.link_button("▶️ Run now", url="https://github.com/swanepoelchristo/milkbox-ai/actions", help="Open Actions and dispatch Reg Watch")
    with cols[1]:
        st.link_button("📝 Edit watchlist.yaml", url="https://github.com/swanepoelchristo/milkbox-ai/blob/main/standards/watchlist.yaml")

    with cols[2]:
        st.caption("Secrets supported (optional): " + ", ".join([f"`{s}`" for s in SECRETS_HINT]))

    with st.expander("📦 Current state (`reg_state.json`)", expanded=False):
        data = read_json(REG_STATE)
        if data:
            st.json(data)
        else:
            st.info("No `reg_state.json` yet. Trigger the Action once, then refresh.")

    st.subheader("🧾 Latest watch log")
    log_txt = read_text(WATCH_LOG)
    if log_txt.strip():
        st.code(log_txt, language="markdown")
    else:
        st.info("No `watch_log.md` yet. Trigger the Action once, then refresh.")

def ui_departments():
    st.subheader("🏭 Departments")
    depts = get_departments()
    if not depts:
        st.warning("No departments found. Add them in `standards/departments.yaml`.")
        return

    # Sidebar style picker
    names = [f"{d.get('name','(unnamed)')}  —  {d.get('key')}" for d in depts]
    idx = st.selectbox("Choose a department", range(len(depts)), format_func=lambda i: names[i])
    d = depts[idx]

    st.markdown(f"### {d.get('name','Department')}")
    meta_cols = st.columns(3)
    with meta_cols[0]:
        st.metric("Owner", d.get("owner", "—"))
    with meta_cols[1]:
        sop_dir_rel = d.get("sop_dir", "")
        sop_dir_abs = (REPO_ROOT / sop_dir_rel).resolve()
        st.metric("SOP folder", sop_dir_rel or "—")
    with meta_cols[2]:
        inbox = d.get("inbox_url", "")
        if inbox:
            st.link_button("📤 Open department drive", inbox)
        else:
            st.button("📤 Set department drive (URL)", disabled=True, help="Add `inbox_url` in departments.yaml or store it as a secret later.")

    expected = d.get("expected_sops", [])
    sop_dir_rel = d.get("sop_dir", "")
    sop_dir_abs = (REPO_ROOT / sop_dir_rel).resolve() if sop_dir_rel else None
    found_files = list_sops(sop_dir_abs) if sop_dir_abs else []

    # Make an index of file basenames for rough matching (so 'SOP-001 Personal Hygiene.pdf' counts)
    found_names = {Path(f).stem for f in found_files}

    st.markdown("#### 📚 SOP checklist")
    if not expected:
        st.info("No expected SOP list provided in departments.yaml.")
    else:
        ok, miss = [], []
        for sop in expected:
            # mark as present if any file stem contains the start of SOP title
            present = any(sop.lower().split()[0] in s.lower() for s in found_names)  # simple heuristic on the prefix
            (ok if present else miss).append(sop)

        if ok:
            st.success("Present:")
            st.write("\n".join([f"• {x}" for x in ok]))
        if miss:
            st.warning("Missing:")
            st.write("\n".join([f"• {x}" for x in miss]))
            st.caption("Place files under the department SOP folder to resolve (see path shown above).")

    with st.expander("🔎 SOP files detected in repository", expanded=False):
        if found_files:
            st.write("\n".join([f"- `{f}`" for f in found_files]))
        else:
            st.info("No SOP files found yet in this department folder.")

def render():
    st.title("Milky Roads AI — Food Safety")
    ui_quick_access()
    st.divider()
    ui_reg_watch()
    st.divider()
    ui_departments()
