import csv
import io
from datetime import datetime, date
from typing import Dict, List, Optional

import streamlit as st

APP_KEY = "milky_food_safety_state_v1"

# -----------------------------
# Small helpers
# -----------------------------
def _init_state():
    if APP_KEY not in st.session_state:
        st.session_state[APP_KEY] = {
            # Records
            "temps": [],        # {dt, area, product, reading_c, user, note}
            "ssop": [],         # {dt, zone, task, pass_fail, user, note}
            "lots": [],         # {dt, product, lot, supplier, qty, unit, use_by, received_ok, note}
            "incidents": [],    # {dt, type, product, lot, description, action, user}

            # Settings
            "brand": "Milky Roads AI — Food Safety",
            "site": "Milky Roads Dairy",
            "areas": ["Receiving", "Cooler", "Freezer", "Processing", "Shipping", "Hot Hold", "Cold Hold"],
            "ssop_zones": ["Raw", "RTE", "Packaging", "Utensils", "CIP"],
            "ssop_tasks": ["Pre-Op Clean", "Mid-Shift Clean", "Post-Op Clean", "Sanitizer Check", "Allergen Clean"],

            # "House with rooms": Departments → SOP links/files
            # Each dept: { name, description, sop_links: [ {title, url} ] }
            "departments": [
                {"name": "Smalls (Artisan Cheeses)", "description": "Fancy cheese room", "sop_links": []},
                {"name": "Production", "description": "Main production floor", "sop_links": []},
                {"name": "Packaging", "description": "Primary & secondary packaging", "sop_links": []},
                {"name": "Warehouse", "description": "Cooler/Freezer storage & shipping", "sop_links": []},
            ],

            # Regulation watcher
            # Store the official URL + note + last_checked timestamp
            "reg_watch": {
                "document_name": "National Food Safety Regulation",
                "official_url": "",         # you paste the official link here
                "note": "We track this URL for amendments.",
                "last_checked_at": None,    # set when you click "Check now"
                "last_seen_hash": None,     # reserved if we later do hashing
            },
        }


def _csv_bytes(rows: List[Dict], header: List[str]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=header)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    return buf.getvalue().encode("utf-8")


def _section_title(title: str, emoji: str = ""):
    if emoji:
        st.subheader(f"{emoji} {title}")
    else:
        st.subheader(title)


# -----------------------------
# Tabs
# -----------------------------
def _tab_temperatures(S: Dict):
    _section_title("Temperature Logs", "🌡️")
    with st.form("temp_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            dt = st.datetime_input("Date & time", datetime.now())
            area = st.selectbox("Area", options=S["areas"])
        with c2:
            product = st.text_input("Product / Item", placeholder="e.g. Milk")
            reading = st.number_input("Reading (°C)", value=4.0, step=0.1, format="%.1f")
        with c3:
            user = st.text_input("User / Initials", placeholder="AB")
            note = st.text_input("Note", placeholder="(optional)")
        submitted = st.form_submit_button("Add temperature")
    if submitted:
        S["temps"].append({
            "dt": dt.isoformat(timespec="minutes"),
            "area": area,
            "product": product.strip(),
            "reading_c": reading,
            "user": user.strip(),
            "note": note.strip(),
        })
        st.success("Temperature added.")

    st.divider()
    st.caption("Today’s temperatures")
    todays = [r for r in S["temps"] if r["dt"].startswith(date.today().isoformat())]
    if todays:
        st.dataframe(todays, use_container_width=True, hide_index=True)
    else:
        st.info("No temperatures recorded today.")


def _tab_sanitation(S: Dict):
    _section_title("Sanitation (SSOP)", "🧽")
    with st.form("ssop_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            dt = st.datetime_input("Date & time", datetime.now(), key="ssop_dt")
            zone = st.selectbox("Zone", options=S["ssop_zones"])
        with c2:
            task = st.selectbox("Task", options=S["ssop_tasks"])
            result = st.selectbox("Result", options=["Pass", "Fail"])
        with c3:
            user = st.text_input("User / Initials", placeholder="AB", key="ssop_user")
            note = st.text_input("Note", placeholder="(optional)", key="ssop_note")
        submitted = st.form_submit_button("Add sanitation record")
    if submitted:
        S["ssop"].append({
            "dt": dt.isoformat(timespec="minutes"),
            "zone": zone,
            "task": task,
            "pass_fail": result,
            "user": user.strip(),
            "note": note.strip(),
        })
        st.success("Sanitation record added.")

    st.divider()
    st.caption("Recent sanitation checks")
    if S["ssop"]:
        st.dataframe(S["ssop"][-50:], use_container_width=True, hide_index=True)
    else:
        st.info("No sanitation records yet.")


def _tab_lots(S: Dict):
    _section_title("Lots & Traceability", "🏷️")
    with st.form("lot_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            dt = st.date_input("Date", value=date.today(), key="lot_dt")
            product = st.text_input("Product", placeholder="e.g. Mozzarella")
        with c2:
            lot = st.text_input("Lot / Batch", placeholder="LOT-12345")
            supplier = st.text_input("Supplier", placeholder="DairyCo")
        with c3:
            qty = st.number_input("Quantity", min_value=0.0, value=100.0, step=1.0)
            unit = st.text_input("Unit", value="kg")
        c4, c5 = st.columns(2)
        with c4:
            use_by = st.date_input("Use by / Expiry", value=date.today())
        with c5:
            received_ok = st.selectbox("Receiving check", options=["OK", "Hold", "Reject"], index=0)
        note = st.text_input("Note", placeholder="(optional)")
        submitted = st.form_submit_button("Add lot")
    if submitted:
        S["lots"].append({
            "dt": dt.isoformat(),
            "product": product.strip(),
            "lot": lot.strip(),
            "supplier": supplier.strip(),
            "qty": qty,
            "unit": unit.strip(),
            "use_by": use_by.isoformat(),
            "received_ok": received_ok,
            "note": note.strip(),
        })
        st.success("Lot added.")

    st.divider()
    st.caption("Recent lots")
    if S["lots"]:
        st.dataframe(S["lots"][-100:], use_container_width=True, hide_index=True)
    else:
        st.info("No lots recorded yet.")


def _tab_incidents(S: Dict):
    _section_title("Incidents / Recall", "⚠️")
    with st.form("inc_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            dt = st.datetime_input("Date & time", datetime.now(), key="inc_dt")
            type_ = st.selectbox("Type", options=["Deviation", "Customer Complaint", "Recall", "Other"])
        with c2:
            product = st.text_input("Product", placeholder="(optional)")
            lot = st.text_input("Lot / Batch", placeholder="(optional)")
        with c3:
            user = st.text_input("User / Initials", placeholder="AB", key="inc_user")
        description = st.text_area("Description / Findings")
        action = st.text_area("Corrective action")
        submitted = st.form_submit_button("Add incident")
    if submitted:
        S["incidents"].append({
            "dt": dt.isoformat(timespec="minutes"),
            "type": type_,
            "product": product.strip(),
            "lot": lot.strip(),
            "description": description.strip(),
            "action": action.strip(),
            "user": user.strip(),
        })
        st.success("Incident added.")

    st.divider()
    st.caption("Recent incidents")
    if S["incidents"]:
        st.dataframe(S["incidents"][-50:], use_container_width=True, hide_index=True)
    else:
        st.info("No incidents recorded yet.")


def _tab_export(S: Dict):
    _section_title("Export CSVs", "📤")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Temperature Logs")
        tmp_hdr = ["dt", "area", "product", "reading_c", "user", "note"]
        st.download_button(
            "Download temperatures (CSV)",
            data=_csv_bytes(S["temps"], tmp_hdr),
            file_name=f"milkyroads_temps_{date.today()}.csv",
            mime="text/csv",
        )
        st.write("Sanitation (SSOP)")
        ssop_hdr = ["dt", "zone", "task", "pass_fail", "user", "note"]
        st.download_button(
            "Download sanitation (CSV)",
            data=_csv_bytes(S["ssop"], ssop_hdr),
            file_name=f"milkyroads_sanitation_{date.today()}.csv",
            mime="text/csv",
        )
    with col2:
        st.write("Lots & Traceability")
        lot_hdr = ["dt", "product", "lot", "supplier", "qty", "unit", "use_by", "received_ok", "note"]
        st.download_button(
            "Download lots (CSV)",
            data=_csv_bytes(S["lots"], lot_hdr),
            file_name=f"milkyroads_lots_{date.today()}.csv",
            mime="text/csv",
        )
        st.write("Incidents / Recall")
        inc_hdr = ["dt", "type", "product", "lot", "description", "action", "user"]
        st.download_button(
            "Download incidents (CSV)",
            data=_csv_bytes(S["incidents"], inc_hdr),
            file_name=f"milkyroads_incidents_{date.today()}.csv",
            mime="text/csv",
        )
    st.caption("Tip: For long-term storage, we can add a Google Sheet or DB later.")


def _tab_settings(S: Dict):
    _section_title("Settings — House, Rooms & Watcher", "⚙️")

    # Branding & site
    st.markdown("### Branding")
    S["brand"] = st.text_input("App title", value=S["brand"])
    S["site"] = st.text_input("Site / Facility name", value=S["site"])

    st.markdown("---")
    st.markdown("### Areas & Sanitation lists")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Temperature Areas** (comma-separated)")
        areas = st.text_area("Areas", value=", ".join(S["areas"]))
        if st.button("Save areas"):
            S["areas"] = [a.strip() for a in areas.split(",") if a.strip()]
            st.success("Areas saved.")
    with col2:
        st.write("**SSOP Zones** (comma-separated)")
        zones = st.text_area("Zones", value=", ".join(S["ssop_zones"]), key="zones")
        st.write("**SSOP Tasks** (comma-separated)")
        tasks = st.text_area("Tasks", value=", ".join(S["ssop_tasks"]), key="tasks")
        if st.button("Save SSOP lists"):
            S["ssop_zones"] = [z.strip() for z in zones.split(",") if z.strip()]
            S["ssop_tasks"] = [t.strip() for t in tasks.split(",") if t.strip()]
            st.success("SSOP lists saved.")

    # Departments (House → Rooms)
    st.markdown("---")
    st.markdown("### Departments & SOP drawers (House → Rooms)")
    for i, d in enumerate(S["departments"]):
        with st.expander(f"🏠 {d['name']}", expanded=False):
            d["name"] = st.text_input("Department name", value=d["name"], key=f"dept_name_{i}")
            d["description"] = st.text_input("Short description", value=d["description"], key=f"dept_desc_{i}")

            st.write("**SOP links**")
            # Show existing
            if d["sop_links"]:
                for j, link in enumerate(d["sop_links"]):
                    cols = st.columns([3, 5, 1])
                    with cols[0]:
                        link["title"] = st.text_input("Title", value=link["title"], key=f"d{i}_t{j}")
                    with cols[1]:
                        link["url"] = st.text_input("URL (Drive/SharePoint/etc.)", value=link["url"], key=f"d{i}_u{j}")
                    with cols[2]:
                        if st.button("🗑", key=f"d{i}_del{j}"):
                            d["sop_links"].pop(j)
                            st.experimental_rerun()
            else:
                st.caption("No SOPs yet for this department.")

            st.write("**Add new SOP link**")
            new_t = st.text_input("New SOP title", key=f"d{i}_new_title")
            new_u = st.text_input("New SOP URL", key=f"d{i}_new_url")
            if st.button("➕ Add SOP link", key=f"d{i}_add"):
                if new_t.strip() and new_u.strip():
                    d["sop_links"].append({"title": new_t.strip(), "url": new_u.strip()})
                    st.success("SOP link added.")
                    st.experimental_rerun()

    # Regulation Watcher (paste official URL, "Check now")
    st.markdown("---")
    st.markdown("### Regulation Watcher")
    rw = S["reg_watch"]
    rw["document_name"] = st.text_input("Document name", value=rw["document_name"])
    rw["official_url"] = st.text_input("Official source URL (paste the regulator’s link)", value=rw["official_url"])
    rw["note"] = st.text_input("Note", value=rw["note"])

    cols = st.columns([1, 2])
    with cols[0]:
        if st.button("🔎 Check now"):
            # We don’t change anything; just record a check time.
            rw["last_checked_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
            st.success("Recorded a check. (For true background monitoring, ask the assistant to set a reminder agent.)")
    with cols[1]:
        st.write("**Last checked at:**", rw["last_checked_at"] or "—")

    st.caption("For automatic background checks & alerts, tell the assistant the official URL and how often to check; you’ll be notified here in chat if it changes.")


# -----------------------------
# Main entry
# -----------------------------
def render():
    _init_state()
    S = st.session_state[APP_KEY]

    st.header(S["brand"])
    st.caption("Temperatures • Sanitation • Traceability • Incidents • Exports • Doc Library • Regulation Watcher")

    t1, t2, t3, t4, t5, t6 = st.tabs([
        "🌡️ Temperatures",
        "🧽 Sanitation",
        "🏷️ Lots",
        "⚠️ Incidents",
        "📤 Export",
        "⚙️ Settings"
    ])

    with t1: _tab_temperatures(S)
    with t2: _tab_sanitation(S)
    with t3: _tab_lots(S)
    with t4: _tab_incidents(S)
    with t5: _tab_export(S)
    with t6: _tab_settings(S)
