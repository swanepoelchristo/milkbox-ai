# streamlit_app/tools/leads.py
"""
CSV-backed Leads Tracker (Streamlit)

- Saves to: data/leads.csv  (ignored by git; add `data/*.csv` to .gitignore)
- Designed to be import-safe for CI smoke (no code runs at import time).
- If pandas isn't installed, the app shows an instruction instead of crashing.

Quick run:
    python -m streamlit run streamlit_app/tools/leads.py
"""

from __future__ import annotations
from pathlib import Path
from datetime import datetime
import streamlit as st

# Lazy/optional pandas for CI import safety
try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover
    pd = None  # type: ignore

DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "leads.csv"

COLUMNS = ["created_at", "name", "email", "company", "source", "status", "notes"]
STATUS_CHOICES = ["New", "Contacted", "Qualified", "Won", "Lost"]
SOURCE_CHOICES = ["Website", "Referral", "LinkedIn", "Inbound", "Outbound", "Event", "Other"]


# ---------- Storage helpers ----------
def _empty_df():
    assert pd is not None, "pandas required at runtime"
    return pd.DataFrame(columns=COLUMNS)  # type: ignore[attr-defined]


def _ensure_schema(df):
    """Add any missing columns and enforce column order."""
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = ""
    # reorder safely
    return df[[c for c in COLUMNS if c in df.columns]]


def _load_df():
    """Read CSV if present; otherwise return an empty DataFrame."""
    assert pd is not None, "pandas required at runtime"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        return _empty_df()

    try:
        df = pd.read_csv(DATA_FILE)  # type: ignore[attr-defined]
    except Exception as e:
        st.error(f"Couldn't read {DATA_FILE}: {e}")
        st.info("Starting with a new empty table. (Tip: close the CSV in Excel if it's open.)")
        return _empty_df()
    return _ensure_schema(df)


def _save_df(df):
    """Persist CSV with friendly error messages."""
    try:
        df.to_csv(DATA_FILE, index=False)  # type: ignore[attr-defined]
        st.success(f"Saved to {DATA_FILE}", icon="✅")
    except PermissionError:
        st.error("Save failed: the CSV is probably open in another program (e.g., Excel). Close it and try again.")
    except Exception as e:
        st.error(f"Save failed: {e}")


# ---------- UI ----------
def app():
    st.title("Leads Tracker")
    st.caption("Capture leads, filter/search, update status, and download CSV. File: `data/leads.csv`")

    # Guard: require pandas for runtime
    if pd is None:
        st.warning(
            "This tool needs **pandas**. Install it, then refresh:\n\n"
            "```bash\npip install pandas\n```"
        )
        return

    df = _load_df()

    # First-run hint
    if df.empty and not DATA_FILE.exists():
        st.info("No leads yet. Add your first lead with the form below — the CSV will be created automatically.")

    # --- New lead form
    st.subheader("Add a lead")
    with st.form("new_lead", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("Name*", placeholder="Jane Doe")
        email = col2.text_input("Email", placeholder="jane@example.com")
        company = col1.text_input("Company / Org", placeholder="Acme Ltd")
        source = col2.selectbox("Source", SOURCE_CHOICES, index=0)
        status = col1.selectbox("Status", STATUS_CHOICES, index=0)
        notes = st.text_area("Notes", placeholder="Context, next steps, etc.")
        submitted = st.form_submit_button("Add lead")

    if submitted:
        if not name.strip() and not email.strip():
            st.error("Please add at least a **Name** or an **Email**.")
        else:
            # simple de-dupe by email (if provided)
            if email.strip():
                exists = (df["email"].astype(str).str.lower() == email.strip().lower()).any()
                if exists:
                    st.warning("A lead with this email already exists. Saving a duplicate anyway.", icon="⚠️")

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
            df = _ensure_schema(df)
            _save_df(df)
            st.success(f"Added lead: {row['name'] or row['email'] or '(no name)'}")

    # --- Filters
    with st.expander("Filters", expanded=True):
        q = st.text_input("Search (name, email, company, notes)")
        status_filter = st.multiselect("Status", STATUS_CHOICES, default=STATUS_CHOICES)
        src_values = sorted([s for s in df["source"].dropna().unique().tolist() if s])
        source_filter = st.multiselect("Source", src_values, default=src_values)
        if st.button("Reset filters"):
            st.experimental_rerun()

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

    st.subheader(f"Leads ({len(filtered)})")
    if filtered.empty:
        st.info("No rows match your filters.")
    st.dataframe(filtered, use_container_width=True)

    # --- Download / Upload
    st.write("### CSV")
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered CSV", csv_bytes, "leads.csv", "text/csv")

    uploaded = st.file_uploader("Optional: upload a leads CSV to append", type=["csv"])
    if uploaded is not None:
        try:
            add_df = pd.read_csv(uploaded)  # type: ignore[attr-defined]
            add_df = _ensure_schema(add_df)
            df = pd.concat([df, add_df], ignore_index=True)  # type: ignore[attr-defined]
            df = _ensure_schema(df)
            _save_df(df)
            st.success(f"Imported {len(add_df)} rows from uploaded CSV.")
        except Exception as e:
            st.error(f"Import failed: {e}")

    # --- Quick status update
    if not df.empty:
        st.subheader("Quick Update")
        # Use filtered view for picking rows to update
        options = list(filtered.index)
        labels = [f"{i}: {filtered.loc[i, 'name']}  [{filtered.loc[i, 'status']}]" for i in options]
        pick = st.selectbox("Pick a row", options, format_func=lambda i: labels[options.index(i)])
        new_status = st.selectbox("New status", STATUS_CHOICES)

        c1, c2 = st.columns(2)
        if c1.button("Update status"):
            df.loc[pick, "status"] = new_status
            _save_df(df)
            st.success("Status updated!")

        if c2.button("Delete selected row"):
            df = df.drop(index=pick)
            df = df.reset_index(drop=True)
            _save_df(df)
            st.success("Row deleted.")

    st.caption("Tip: If the page is blank when running directly, make sure this file ends with the "
               "`if __name__ == '__main__': app()` block.")


if __name__ == "__main__":
    app()
