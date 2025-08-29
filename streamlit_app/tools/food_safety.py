import io
import json
import os
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st
import yaml

# ───────────────────────── Paths ─────────────────────────
APP_ROOT = Path(__file__).resolve().parents[1]     # streamlit_app/
REPO_ROOT = APP_ROOT.parent                         # repo root
STANDARDS_DIR = REPO_ROOT / "standards"

WATCHLIST   = STANDARDS_DIR / "watchlist.yaml"
REG_STATE   = STANDARDS_DIR / "reg_state.json"
WATCH_LOG   = STANDARDS_DIR / "watch_log.md"
DEPT_CFG    = STANDARDS_DIR / "departments.yaml"
LOC_YAML    = STANDARDS_DIR / "locations.yaml"     # <— NEW: Step 2

SECRETS_HINT = [
    "DOC_ISO22000_URL",
    "DOC_HACCP_URL",
    "DOC_LOCAL_REG_URL",
    "DOC_SOP_INDEX_URL",
]

# ─────────────────────── Helpers ────────────────────────
def read_yaml(p: Path) -> Optional[dict]:
    try:
        if not p.exists(): return None
        with p.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return None

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""

def read_json(p: Path) -> dict:
    if not p.exists(): return {}
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return {}

def get_departments() -> List[dict]:
    data = read_yaml(DEPT_CFG) or {}
    return data.get("departments", [])

def list_files(base: Path) -> List[Path]:
    if not base or not base.exists(): return []
    return [p for p in base.rglob("*") if p.is_file()]

def has_secret(name: str) -> bool:
    try: return st.secrets.get(name) is not None
    except Exception: return False

def zip_files(files: List[Path]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            arc = f.relative_to(REPO_ROOT).as_posix()
            z.write(f, arc)
    buf.seek(0)
    return buf.read()

def load_locations_yaml() -> dict:
    """Step 2: read standards/locations.yaml (fallback after secrets)."""
    try:
        return yaml.safe_load(LOC_YAML.read_text(encoding="utf-8")) if LOC_YAML.exists() else {}
    except Exception:
        return {}

# ─────────────────────── UI Blocks ──────────────────────
def ui_quick_access():
    """Quick links resolve in priority: Secrets → locations.yaml (Step 2)."""
    locs = load_locations_yaml()

    iso   = st.secrets.get("DOC_ISO22000_URL") or locs.get("DOC_ISO22000_URL", "")
    haccp = st.secrets.get("DOC_HACCP_URL")    or locs.get("DOC_HACCP_URL", "")
    local = st.secrets.get("DOC_LOCAL_REG_URL") or locs.get("DOC_LOCAL_REG_URL", "")
    sopix = st.secrets.get("DOC_SOP_INDEX_URL") or locs.get("DOC_SOP_INDEX_URL", "")

    with st.expander("Quick access — Documents & SOPs", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("📄 **ISO 22000**")
            if iso: st.link_button("Open", iso)
            st.caption("Source: Secret or locations.yaml")
        with col2:
            st.write("📄 **HACCP**")
            if haccp: st.link_button("Open", haccp)
            st.caption("Source: Secret or locations.yaml")
        with col3:
            st.write("🏛️ **Local Regulation**")
            if local: st.link_button("Open", local)
            st.caption("Source: Secret or locations.yaml")

        st.write("🗂️ **Company SOP Index**")
        if sopix: st.link_button("Open SOP Index", sopix)
        st.caption("Use Home → Set Document Locations to configure if secrets not set.")

def ui_reg_watch():
    st.subheader("🔬 Regulatory Watch")
    st.caption(
        "Reads `standards/watch_log.md` and `standards/reg_state.json`. "
        "The GitHub Action **Regulatory Watch** is scheduled and can be run on demand."
    )
    cols = st.columns([1,1,3])
    with cols[0]:
        st.link_button("▶️ Run now", "https://github.com/swanepoelchristo/milkbox-ai/actions")
    with cols[1]:
        st.link_button("📝 Edit watchlist.yaml", "https://github.com/swanepoelchristo/milkbox-ai/blob/main/standards/watchlist.yaml")
    with cols[2]:
        st.caption("Secrets supported: " + ", ".join([f"`{s}`" for s in SECRETS_HINT]))

    with st.expander("📦 Current state (`reg_state.json`)", expanded=False):
        data = read_json(REG_STATE)
        st.json(data) if data else st.info("No `reg_state.json` yet. Trigger the Action once, then refresh.")

    st.subheader("🧾 Latest watch log")
    log_txt = read_text(WATCH_LOG)
    st.code(log_txt, language="markdown") if log_txt.strip() else st.info("No `watch_log.md` yet. Trigger the Action once, then refresh.")

def ui_departments():
    st.subheader("🏭 Departments")
    depts = get_departments()
    if not depts:
        st.warning("No departments found. Add them in `standards/departments.yaml`.")
        return

    names = [f"{d.get('name','(unnamed)')}  —  {d.get('key')}" for d in depts]
    idx = st.selectbox("Choose a department", range(len(depts)), format_func=lambda i: names[i])
    d = depts[idx]

    st.markdown(f"### {d.get('name','Department')}")
    meta_cols = st.columns(3)
    sop_dir_rel = d.get("sop_dir", "")
    sop_dir_abs = (REPO_ROOT / sop_dir_rel).resolve() if sop_dir_rel else None
    with meta_cols[0]: st.metric("Owner", d.get("owner", "—"))
    with meta_cols[1]: st.metric("SOP folder", sop_dir_rel or "—")
    with meta_cols[2]:
        inbox = d.get("inbox_url", "")
        st.link_button("📤 Open department drive", inbox) if inbox else st.button("📤 Set department drive (URL)", disabled=True)

    expected = d.get("expected_sops", [])
    found_files = list_files(sop_dir_abs)
    found_names = {p.stem.lower() for p in found_files}

    st.markdown("#### 📚 SOP checklist")
    if not expected:
        st.info("No expected SOP list provided in departments.yaml.")
    else:
        ok, miss = [], []
        for sop in expected:
            token = sop.split()[0].lower()
            present = any(token in s for s in found_names)
            (ok if present else miss).append(sop)

        if ok:
            st.success("Present:")
            st.write("\n".join([f"• {x}" for x in ok]))
        if miss:
            st.warning("Missing:")
            st.write("\n".join([f"• {x}" for x in miss]))
            st.caption("Place files under the department SOP folder to resolve.")

    with st.expander("🔎 SOP files detected in repository", expanded=False):
        if found_files:
            st.write("\n".join([f"- `{p.relative_to(REPO_ROOT).as_posix()}`" for p in found_files]))
        else:
            st.info("No SOP files found yet in this department folder.")

def ui_production_packet():
    st.subheader("📦 Production Day Packet")
    depts = get_departments()
    if not depts:
        st.info("Add departments in `standards/departments.yaml` first.")
        return

    names = [f"{d.get('name','(unnamed)')}  —  {d.get('key')}" for d in depts]
    idx = st.selectbox("Department for packet", range(len(depts)), format_func=lambda i: names[i], key="pkt_dept")
    d = depts[idx]

    packet_cfg = (d.get("packet") or {})
    patts = packet_cfg.get("include_patterns", ["SOP-*.pdf","PRP-*.pdf"])
    extras = packet_cfg.get("extra_paths", [])

    date = st.date_input("Production date")
    sop_dir_rel = d.get("sop_dir","")
    sop_dir_abs = (REPO_ROOT / sop_dir_rel).resolve() if sop_dir_rel else None

    files: List[Path] = []
    if sop_dir_abs and sop_dir_abs.exists():
        for patt in patts:
            files.extend(sop_dir_abs.rglob(patt))
    for ep in extras:
        for p in (REPO_ROOT / ep).parent.rglob(Path(ep).name):
            if p.is_file(): files.append(p)

    files = sorted({f.resolve() for f in files if f.is_file()})

    st.caption("Preview of files that will be packaged:")
    if files:
        st.write("\n".join([f"- `{f.relative_to(REPO_ROOT).as_posix()}`" for f in files]))
        zbytes = zip_files(files)
        fname = f"{d.get('key','dept')}_{date.isoformat()}_packet.zip"
        st.download_button("⬇️ Download Packet (ZIP)", data=zbytes, file_name=fname, mime="application/zip")
    else:
        st.info("No matching files yet. Add SOP/PRP files to the department folder or define extra_paths.")

# ─────────────────────── Page entry ─────────────────────
def render():
    st.title("Milky Roads AI — Food Safety")
    ui_quick_access()      # Step 2: reads Secrets → locations.yaml
    st.divider()
    ui_reg_watch()
    st.divider()
    ui_departments()
    st.divider()
    ui_production_packet()
