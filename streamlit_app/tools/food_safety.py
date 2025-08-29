import hashlib
import io
import json
import time
from datetime import datetime, date
from typing import Dict, Any, List, Tuple, Optional

import requests
import streamlit as st


# ─────────────────────────────────────────────────────────
# Helpers & state
# ─────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _download_csv(filename: str, rows: List[Dict[str, Any]]):
    # Build CSV in-memory (no pandas dependency)
    if not rows:
        st.info("Nothing to export yet.")
        return
    headers = list(rows[0].keys())
    buf = io.StringIO()
    buf.write(",".join(headers) + "\n")
    for r in rows:
        line = []
        for h in headers:
            v = r.get(h, "")
            # Escape commas and quotes
            if isinstance(v, (dict, list)):
                v = json.dumps(v)
            s = str(v).replace('"', '""')
            if "," in s or '"' in s or "\n" in s:
                s = f'"{s}"'
            line.append(s)
        buf.write(",".join(line) + "\n")
    st.download_button("Download CSV", buf.getvalue().encode("utf-8"), file_name=filename, mime="text/csv")


def _download_json(filename: str, data: Any):
    st.download_button("Download JSON", json.dumps(data, indent=2).encode("utf-8"),
                       file_name=filename, mime="application/json")


def _init_state():
    ss = st.session_state
    ss.setdefault("fs_temperatures", [])   # list of dicts
    ss.setdefault("fs_sanitation", [])     # list of completed sanitation entries
    ss.setdefault("fs_sanitation_tasks", [
        {"name": "Clean vats", "freq": "Daily"},
        {"name": "Sanitize knives", "freq": "Daily"},
        {"name": "Deep clean aging room", "freq": "Weekly"},
    ])
    ss.setdefault("fs_lots", [])           # list of dicts
    ss.setdefault("fs_incidents", [])      # list of dicts
    ss.setdefault("fs_depts", {            # house → rooms → drawers (SOPs)
        "Milk Intake": {"SOPs": []},
        "Production (Cook/Cut/Press)": {"SOPs": []},
        "Aging Rooms": {"SOPs": []},
        "Packaging": {"SOPs": []},
        "Dispatch": {"SOPs": []},
        "Lab": {"SOPs": []},
    })
    ss.setdefault("fs_reg_watch", {
        "mode": "url",       # "url" or "file"
        "url": "",
        "last_etag": "",
        "last_modified": "",
        "last_hash": "",     # for uploaded file content hash
        "last_check": "",
    })


# ─────────────────────────────────────────────────────────
# Sections
# ─────────────────────────────────────────────────────────

def home_ui():
    st.subheader("Milky Roads AI — Food Safety (Home)")
    st.write(
        "This tool organizes **temperature logs**, **sanitation (SSOP)**, **lots/traceability**, "
        "**incidents/CAPA**, and a **Food Safety House** where each department has an SOP drawer. "
        "Use the sidebar to open a section."
    )
    st.info(
        "Tip: everything is stored in your session while you work. Use **Export** to download CSV/JSON "
        "for your records or to import elsewhere."
    )


def temperatures_ui():
    st.subheader("Temperature Logs")
    with st.form("temp_form", clear_on_submit=False):
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        dt = col1.date_input("Date", date.today())
        tm = col2.time_input("Time", datetime.now().time())
        probe = col3.text_input("Probe/Sensor ID", "Probe-1")
        loc = col4.text_input("Location/Unit", "Milk vat")

        col5, col6 = st.columns([1, 1])
        temp_c = col5.number_input("Temperature (°C)", value=4.0, step=0.1)
        operator = col6.text_input("Operator", "")

        notes = st.text_area("Notes", "")
        submitted = st.form_submit_button("Add record")
        if submitted:
            st.session_state.fs_temperatures.append({
                "timestamp": f"{dt} {tm}",
                "probe": probe,
                "location": loc,
                "temp_c": temp_c,
                "operator": operator,
                "notes": notes
            })
            st.success("Temperature record added.")

    st.divider()
    st.write("#### Latest records")
    rows = st.session_state.fs_temperatures[-50:][::-1]
    if rows:
        st.table(rows)
        _download_csv("temperatures.csv", rows)
    else:
        st.info("No temperature records yet.")


def sanitation_ui():
    st.subheader("SSOP / Sanitation")

    with st.expander("Configure tasks (admin)", expanded=False):
        st.caption("Add or remove routine SSOP tasks that appear below.")
        tname = st.text_input("New task name", "")
        tfreq = st.selectbox("Frequency", ["Daily", "Weekly", "Monthly"], index=0)
        add_task = st.button("Add task")
        if add_task and tname.strip():
            st.session_state.fs_sanitation_tasks.append({"name": tname.strip(), "freq": tfreq})
            st.success("Task added.")
        if st.session_state.fs_sanitation_tasks:
            st.write("Current tasks")
            st.table(st.session_state.fs_sanitation_tasks)

    st.write("#### Perform SSOP")
    with st.form("ssop_form", clear_on_submit=True):
        the_date = st.date_input("Date", date.today())
        the_time = st.time_input("Time", datetime.now().time())
        operator = st.text_input("Operator", "")
        chem = st.text_input("Chemical(s) Used", "")
        completed = []
        for task in st.session_state.fs_sanitation_tasks:
            done = st.checkbox(f"{task['name']} ({task['freq']})", value=False)
            if done:
                completed.append(task["name"])
        notes = st.text_area("Notes", "")
        sub = st.form_submit_button("Save sanitation record")
        if sub:
            st.session_state.fs_sanitation.append({
                "timestamp": f"{the_date} {the_time}",
                "operator": operator,
                "chemicals": chem,
                "completed": completed,
                "notes": notes
            })
            st.success("Sanitation record saved.")

    st.divider()
    st.write("#### Latest sanitation")
    rows = st.session_state.fs_sanitation[-50:][::-1]
    if rows:
        st.table(rows)
        _download_csv("sanitation.csv", rows)
    else:
        st.info("No sanitation records yet.")


def lots_ui():
    st.subheader("Lots & Traceability")

    with st.form("lot_form", clear_on_submit=True):
        lot_id = st.text_input("Lot ID", "")
        product = st.text_input("Product", "Cheese (specify)")
        mfg_date = st.date_input("Manufacture Date", date.today())
        suppliers = st.text_input("Supplier / Farm codes (comma-separated)", "")
        ingredients = st.text_area("Ingredients (one per line)", "Milk\nCulture\nRennet\nSalt")
        qty = st.text_input("Quantity / Pack info", "")
        sub = st.form_submit_button("Add lot")
        if sub and lot_id.strip():
            st.session_state.fs_lots.append({
                "lot_id": lot_id.strip(),
                "product": product,
                "mfg_date": str(mfg_date),
                "suppliers": [s.strip() for s in suppliers.split(",") if s.strip()],
                "ingredients": [i.strip() for i in ingredients.splitlines() if i.strip()],
                "qty": qty
            })
            st.success("Lot saved.")

    st.divider()
    st.write("#### Lots")
    rows = st.session_state.fs_lots[-100:][::-1]
    if rows:
        st.table(rows)
        _download_csv("lots.csv", rows)
    else:
        st.info("No lots yet.")


def incidents_ui():
    st.subheader("Incidents / CAPA")

    with st.form("incident_form", clear_on_submit=True):
        i_date = st.date_input("Date", date.today())
        i_time = st.time_input("Time", datetime.now().time())
        severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
        area = st.text_input("Area/Dept", "")
        description = st.text_area("Incident Description", "")
        root = st.text_area("Root Cause (if known)", "")
        action = st.text_area("Corrective Action", "")
        proof = st.file_uploader("Attach evidence (optional)", accept_multiple_files=True)
        submit = st.form_submit_button("Save incident")
        if submit:
            files_meta = []
            if proof:
                for f in proof:
                    files_meta.append({"name": f.name, "size": f.size})
            st.session_state.fs_incidents.append({
                "timestamp": f"{i_date} {i_time}",
                "severity": severity,
                "area": area,
                "description": description,
                "root_cause": root,
                "action": action,
                "attachments": files_meta
            })
            st.success("Incident saved.")

    st.divider()
    st.write("#### Incidents")
    rows = st.session_state.fs_incidents[-100:][::-1]
    if rows:
        st.table(rows)
        _download_csv("incidents.csv", rows)
    else:
        st.info("No incidents yet.")


def house_ui():
    st.subheader("Food Safety House — Departments & SOP drawers")
    st.caption("Each department has a drawer where you can drop SOPs or a link to a folder.")

    # Add/rename departments
    with st.expander("Manage departments", expanded=False):
        new_dept = st.text_input("Add a department", "")
        add = st.button("Add department")
        if add and new_dept.strip():
            st.session_state.fs_depts.setdefault(new_dept.strip(), {"SOPs": []})
            st.success("Department added.")

    # Show depts
    for dept_name, meta in st.session_state.fs_depts.items():
        with st.expander(f"🏢 {dept_name}", expanded=False):
            st.write("**SOP Drawer**")
            col1, col2 = st.columns([1, 1])
            # upload SOP
            up = col1.file_uploader(f"Upload SOP for {dept_name}", key=f"sop_upload_{dept_name}")
            link = col2.text_input(f"or link a folder/drive URL", key=f"sop_link_{dept_name}")
            add_sop = st.button(f"Attach to {dept_name}", key=f"attach_{dept_name}")
            if add_sop:
                entry = {"added_at": _now_iso()}
                if up is not None:
                    content = up.read()
                    entry.update({
                        "type": "file",
                        "name": up.name,
                        "size": len(content),
                        "sha256": _hash_bytes(content)
                    })
                elif link.strip():
                    entry.update({
                        "type": "link",
                        "url": link.strip()
                    })
                else:
                    st.warning("Please upload a file or paste a link.")
                    st.stop()
                meta["SOPs"].append(entry)
                st.success("Attached.")

            if meta["SOPs"]:
                st.write("**Current drawer contents**")
                st.table(meta["SOPs"])
            else:
                st.info("Drawer empty.")


def regulation_watcher_ui():
    st.subheader("Regulation Watcher")
    st.caption("Paste the official guideline URL **or** upload the PDF. Click **Check now** to detect changes. "
               "We store ETag/Last-Modified (URL) or content hash (file) in your session to compare.")

    mode = st.radio("Source type", ["URL", "Upload"], index=0, horizontal=True)
    st.session_state.fs_reg_watch["mode"] = "url" if mode == "URL" else "file"

    if mode == "URL":
        url = st.text_input("Regulation URL", st.session_state.fs_reg_watch.get("url", ""))
        st.session_state.fs_reg_watch["url"] = url.strip()
        checked = st.button("Check now")
        if checked and url.strip():
            try:
                r = requests.head(url, timeout=10, allow_redirects=True)
                etag = r.headers.get("ETag", "")
                lm = r.headers.get("Last-Modified", "")
                changed = (etag and etag != st.session_state.fs_reg_watch.get("last_etag")) or \
                          (lm and lm != st.session_state.fs_reg_watch.get("last_modified"))
                st.write(f"ETag: `{etag or '—'}`  •  Last-Modified: `{lm or '—'}`")
                if changed:
                    st.warning("🔔 Update detected for this URL (ETag/Last-Modified changed).")
                else:
                    st.success("No change detected.")
                st.session_state.fs_reg_watch["last_etag"] = etag
                st.session_state.fs_reg_watch["last_modified"] = lm
                st.session_state.fs_reg_watch["last_check"] = _now_iso()
            except Exception as e:
                st.error(f"HEAD request failed: {e}")

    else:
        up = st.file_uploader("Upload the official PDF", type=["pdf"])
        if up:
            content = up.read()
            current_hash = _hash_bytes(content)
            last_hash = st.session_state.fs_reg_watch.get("last_hash", "")
            st.write(f"Current SHA256: `{current_hash}`")
            if last_hash and current_hash != last_hash:
                st.warning("🔔 File content changed (hash differs).")
            elif last_hash:
                st.success("No change detected.")
            else:
                st.info("Baseline saved for this file.")
            st.session_state.fs_reg_watch["last_hash"] = current_hash
            st.session_state.fs_reg_watch["last_check"] = _now_iso()

    st.divider()
    st.write("**Watcher status**")
    st.json(st.session_state.fs_reg_watch)


def export_ui():
    st.subheader("Export Center")
    st.caption("Download snapshots of your current session data.")

    st.write("**Temperatures**")
    _download_csv("temperatures.csv", st.session_state.fs_temperatures)

    st.write("**Sanitation**")
    _download_csv("sanitation.csv", st.session_state.fs_sanitation)

    st.write("**Lots**")
    _download_csv("lots.csv", st.session_state.fs_lots)

    st.write("**Incidents**")
    _download_csv("incidents.csv", st.session_state.fs_incidents)

    st.write("**Departments (House) — JSON**")
    _download_json("departments.json", st.session_state.fs_depts)


# ─────────────────────────────────────────────────────────
# Page
# ─────────────────────────────────────────────────────────

def render():
    st.title("Milky Roads AI — Food Safety")

    _init_state()

    # Local tabs inside the tool
    tab = st.sidebar.radio(
        "Sections",
        [
            "Home",
            "Temperatures",
            "Sanitation (SSOP)",
            "Lots / Traceability",
            "Incidents / CAPA",
            "Departments (House)",
            "Regulation Watcher",
            "Export"
        ],
        index=0
    )

    if tab == "Home":
        home_ui()
    elif tab == "Temperatures":
        temperatures_ui()
    elif tab == "Sanitation (SSOP)":
        sanitation_ui()
    elif tab == "Lots / Traceability":
        lots_ui()
    elif tab == "Incidents / CAPA":
        incidents_ui()
    elif tab == "Departments (House)":
        house_ui()
    elif tab == "Regulation Watcher":
        regulation_watcher_ui()
    elif tab == "Export":
        export_ui()
