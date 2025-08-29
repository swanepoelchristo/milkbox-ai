import os
import io
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple

import requests
import streamlit as st

# -----------------------------
# Helpers: tiny key-value state
# -----------------------------
def _state() -> Dict[str, Any]:
    if "fs_state" not in st.session_state:
        st.session_state.fs_state = {
            # standards registry: { "name": {"url": str|None, "uploaded_name": str|None, "last_checked": iso8601|None, "etag": str|None, "last_modified": str|None} }
            "standards": {},
            # SOP registry: list of dicts (dept/area/type/title/url_or_name/timestamp)
            "sops": [],
        }
    return st.session_state.fs_state

def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _open_link_btn(label: str, url: str, key: str):
    st.link_button(label, url, key=key)

def _pretty_meta(meta: Dict[str, Any]) -> str:
    bits = []
    if meta.get("last_modified"):
        bits.append(f"Last-Modified: {meta['last_modified']}")
    if meta.get("etag"):
        bits.append(f"ETag: {meta['etag']}")
    if meta.get("last_checked"):
        bits.append(f"Checked: {meta['last_checked']}")
    return " • ".join(bits) if bits else "—"

# --------------------------------
# Network: HEAD to check new draft
# --------------------------------
def _head(url: str) -> Tuple[int, Dict[str, str]]:
    try:
        r = requests.head(url, timeout=10, allow_redirects=True)
        return (r.status_code, r.headers or {})
    except Exception:
        return (0, {})

# -----------------------------
# UI: Standards & SOP dashboard
# -----------------------------
def _standards_panel():
    st.subheader("Standards & Monitoring")

    state = _state()

    with st.expander("Register ISO 22000 (official link) or upload a copy", expanded=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            iso_url = st.text_input(
                "ISO 22000 official URL",
                value=state["standards"].get("ISO 22000", {}).get("url", ""),
                placeholder="https://www.iso.org/standard/XXXX.html",
            )
        with col2:
            check_now = st.button("Check for updates", type="secondary")

        uploaded = st.file_uploader("Or upload a local PDF (kept only for this session)", type=["pdf"], accept_multiple_files=False, key="iso_upload")
        saved_name = None
        if uploaded:
            # Save to the ephemeral /tmp (Streamlit Cloud) so we can open/download this session.
            saved_name = f"/tmp/{int(time.time())}_{uploaded.name}"
            with open(saved_name, "wb") as f:
                f.write(uploaded.getbuffer())
            st.success(f"Uploaded: {uploaded.name}")

        # Save changes
        if st.button("Save ISO 22000 entry", type="primary"):
            state["standards"].setdefault("ISO 22000", {})
            entry = state["standards"]["ISO 22000"]
            if iso_url.strip():
                entry["url"] = iso_url.strip()
            if saved_name:
                entry["uploaded_name"] = saved_name
            if "last_checked" not in entry:
                entry["last_checked"] = None
            st.success("Saved ISO 22000 record.")

        # Show the current record + actions
        if "ISO 22000" in state["standards"]:
            entry = state["standards"]["ISO 22000"]
            st.markdown("**Current ISO 22000 record**")
            meta = _pretty_meta(entry)
            st.caption(meta if meta else "—")

            cols = st.columns(3)
            # Open official URL
            if entry.get("url"):
                with cols[0]:
                    _open_link_btn("Open ISO 22000 (URL)", entry["url"], key="open_iso_url")
            # Open uploaded PDF
            if entry.get("uploaded_name") and os.path.exists(entry["uploaded_name"]):
                with cols[1]:
                    st.download_button(
                        "Download uploaded PDF",
                        data=open(entry["uploaded_name"], "rb"),
                        file_name=os.path.basename(entry["uploaded_name"]),
                        mime="application/pdf",
                    )
            with cols[2]:
                if st.button("Clear record"):
                    state["standards"].pop("ISO 22000", None)
                    st.experimental_rerun()

            # Optional: live update check
            if check_now and entry.get("url"):
                code, headers = _head(entry["url"])
                if code >= 200:
                    entry["etag"] = headers.get("ETag") or entry.get("etag")
                    entry["last_modified"] = headers.get("Last-Modified") or entry.get("last_modified")
                    entry["last_checked"] = _now_iso()
                    st.info("Checked ISO link. If ETag/Last-Modified changed since last time, the document likely updated.")
                    st.caption(_pretty_meta(entry))
                else:
                    st.warning("Could not reach the URL just now. Try again later.")

    st.divider()

def _sops_panel():
    st.subheader("House → Rooms → Drawers (Departments / Areas / SOP types)")
    st.caption("Register SOPs by department, area, and document type. Paste a URL or upload a file.")

    state = _state()

    with st.form("sop_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            dept = st.text_input("Department (House)", placeholder="e.g., Small Goods / Cheese Room")
        with c2:
            area = st.text_input("Area (Room)", placeholder="e.g., Packing / Ripening")
        with c3:
            doc_type = st.text_input("Document type (Drawer)", placeholder="e.g., SOP / Work Instruction")

        title = st.text_input("Document title", placeholder="e.g., SOP-PRP-Cleaning-2025")
        url = st.text_input("Document URL (SharePoint/Drive/etc.)", placeholder="https://...")
        file_up = st.file_uploader("Or upload file (PDF/DOCX/XLSX/etc.)", type=None)

        submitted = st.form_submit_button("Add SOP", type="primary")
        if submitted:
            if not (dept and area and doc_type and title):
                st.error("Please fill Department, Area, Document type, and Title.")
            else:
                record = {
                    "dept": dept.strip(),
                    "area": area.strip(),
                    "type": doc_type.strip(),
                    "title": title.strip(),
                    "timestamp": _now_iso(),
                }
                if url.strip():
                    record["href"] = url.strip()
                elif file_up:
                    # Save to /tmp so it can be downloaded in-session
                    tmpname = f"/tmp/{int(time.time())}_{file_up.name}"
                    with open(tmpname, "wb") as f:
                        f.write(file_up.getbuffer())
                    record["href"] = tmpname
                else:
                    record["href"] = None

                state["sops"].append(record)
                st.success("SOP registered ✔")

    # List SOPs (simple grouping)
    if state["sops"]:
        st.markdown("### Registered SOPs")
        # Sort newest first
        for rec in sorted(state["sops"], key=lambda r: r["timestamp"], reverse=True):
            with st.container(border=True):
                st.write(
                    f"**{rec['title']}**  \n"
                    f"Dept: {rec['dept']}  •  Area: {rec['area']}  •  Type: {rec['type']}  \n"
                    f"Added: {rec['timestamp']}"
                )
                if rec.get("href"):
                    if rec["href"].startswith(("http://", "https://")):
                        st.link_button("Open", rec["href"], key=f"open_{rec['timestamp']}")
                    else:
                        if os.path.exists(rec["href"]):
                            st.download_button(
                                "Download",
                                data=open(rec["href"], "rb"),
                                file_name=os.path.basename(rec["href"]),
                            )
                        else:
                            st.caption("Local file no longer available in this session.")
                # Remove button
                if st.button("Remove", key=f"rm_{rec['timestamp']}"):
                    state["sops"] = [x for x in state["sops"] if x["timestamp"] != rec["timestamp"]]
                    st.experimental_rerun()
    else:
        st.info("No SOPs registered yet. Use the form above to add your first record.")

# -----------------------------
# Main render()
# -----------------------------
def render():
    st.header("Milky Roads AI — Food Safety")
    st.caption("ISO 22000 alignment: documented information (7.5), traceability (8.3), and change awareness via update checks.")  # see ISO 22000

    # Tabs for the dashboard. Your existing Temperature/Sanitizer/etc. can be other tabs.
    tab1, tab2 = st.tabs(["Standards & Monitoring", "SOP Registry"])
    with tab1:
        _standards_panel()
    with tab2:
        _sops_panel()

    st.info(
        "Next step (optional): convert the ISO URL watcher into a scheduled job "
        "(e.g., GitHub Actions) that pings daily and posts a notice. For now, use **Check for updates**."
    )
