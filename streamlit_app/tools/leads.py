# streamlit_app/tools/leads.py
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import streamlit as st

# NOTE: We import pandas lazily so CI "import smoke" can pass without pandas installed.
try:
    import pandas as pd  # type: ignore
except Exception:
    pd = None  # CI-friendly: import won't fail; we'll guard in app()

DATA_FILE = Path("data/leads.csv")
COLUMNS = ["created_at", "name", "email", "company", "source", "status", "notes"]
STATUS_CHOICES = ["New", "Contacted", "Qualified", "Won", "Lost"]

def _load_df():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        if DATA_FILE.exists():
            return pd.read_csv(DATA_FILE)  # type: ignore[attr-defined]
        else:
            return pd.DataFrame(columns=COLUMNS)  # type: ignore[attr-defined]
    except Exception:
        return pd.DataFrame(columns=COLUMNS)  # type: ignore[attr-defined]

def _save_df(df):
    df.to_csv(DATA_FILE, index=False)  # type: ignore[attr-defined]

def app():
    st.title("Leads Tracker")
    st.caption("Capture leads, filter/search, update status, and download CSV. Saved at data/leads.csv")

    # Guard: if pandas not installed, show hint and exit gracefully.
    if pd is None:
        st.warning("This tool needs pandas. Run:  pip install pandas")
        return

    df = _load_df()
    # Ensure schema
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = ""

    # --- New lead form
    with st.form("new_lead"):
        col1, col2 = st.columns(2)
        name = col1.text_input("Name")
        email = col2.text_input("Email")
        company = col1.text_input("Company / Org")
        source = col2.selectbox("Source", ["Website", "Referral", "LinkedIn", "Inbound", "Outbound", "Event", "Other"])
        status = col1.selectbox("Status", STATUS_CHOICES, index=0)
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add lead")
    if submitted:
        row = {
            "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "name": name.strip(),
            "email": email.strip(),
            "company": company.strip(),
            "source": source,
            "status": status,
            "notes": notes.strip(),
        }
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)  # type: ignore[attr-defined]
        _save_df(df)
        st.success(f"Added lead: {name or '(no name)'}")

    # --- Filters
    with st.expander("Filters", expanded=True):
        q = st.text_input("Search (name, email, company, notes)")
        status_filter = st.multiselect("Status", STATUS_CHOICES, default=STATUS_CHOICES)
        src_values = sorted([s for s in df["source"].dropna().unique().tolist() if s])
        source_filter = st.multiselect("Source", src_values)

    filtered = df.copy()
    if q:
        ql = q.lower()
        filtered = filtered[
            filtered.apply(
                lambda r: ql in " ".join(str(r[c]) for c in ["name", "email", "company", "notes"]).lower(), axis=1
            )
        ]
    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]
    if source_filter:
        filtered = filtered[filtered["source"].isin(source_filter)]

    st.subheader("Leads")
    st.dataframe(filtered, use_container_width=True)

    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered CSV", csv, "leads.csv", "text/csv")

    # --- Quick status update
    if not filtered.empty:
        st.subheader("Quick Update")
        # build a nice label per row
        options = list(filtered.index)
        labels = [f"{i}: {filtered.loc[i, 'name']}  [{filtered.loc[i, 'status']}]" for i in options]
        pick = st.selectbox("Pick a row", options, format_func=lambda i: labels[options.index(i)])
        new_status = st.selectbox("New status", STATUS_CHOICES)
        if st.button("Update status"):
            df.loc[pick, "status"] = new_status
            _save_df(df)
            st.success("Status updated!")
