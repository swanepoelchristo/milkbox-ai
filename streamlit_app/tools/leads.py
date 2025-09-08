from __future__ import annotations
from pathlib import Path
from datetime import datetime
import streamlit as st

# Import pandas lazily so CI can import this module without pandas installed
try:
    import pandas as pd  # type: ignore
except Exception:
    pd = None  # type: ignore

DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "leads.csv"

COLUMNS = ["created_at", "name", "email", "company", "source", "status", "notes"]
STATUS_CHOICES = ["New", "Contacted", "Qualified", "Won", "Lost"]
SOURCE_CHOICES = ["Website", "Referral", "LinkedIn", "Inbound", "Outbound", "Event", "Other"]


# ---------- storage helpers ----------
def _empty_df():
    assert pd is not None, "pandas required at runtime"
    return pd.DataFrame(columns=COLUMNS)  # type: ignore[attr-defined]


def _ensure_schema(df):
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = ""
    # reorder to our schema where possible
    cols = [c for c in COLUMNS if c in df.columns]
    return df[cols]


def _load_df():
    assert pd is not None, "pandas required at runtime"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        return _empty_df()
    try:
        df = pd.read_csv(DATA_FILE)  # type: ignore[attr-defined]
    except Exception as e:
        st.error(f"Couldn't read {DATA_FILE}: {e}")
        st.info("Starting with an empty table. Tip: close the CSV in Excel if it's open.")
        return _empty_df()
    return _ensure_schema(df)


def _save_df(df):
    try:
        df.to_csv(DATA_FILE, index=False)  # type: ignore[attr-defined]
        st.toast(f"Saved to {DATA_FILE}", icon="✅")
    except PermissionError:
        st.error("Save failed: CSV is open in another program (e.g., Excel). Close it and try again.")
    except Exception as e:
        st.error(f"Save failed: {e}")


# ---------- app ----------
def app():
    # DEBUG — safe to remove later
    st.write(":blue[DEBUG] entering app()")
    st.write(":blue[DEBUG] pandas:", "OK" if pd is not None else "None")
    st.write(":blue[DEBUG] cwd:", Path.cwd(), " csv_exists:", DATA_FILE.exists())

    st.title("Leads Tracker")
    st.caption("Capture leads, filter/search, update status, and download CSV. File: data/leads.csv")

    if pd is None:
        st.warning("This tool needs **pandas**. Install and refresh:\n\n```bash\npip install pandas\n```")
        return

    df = _load_df()
    df = _ensure_schema(df)

    # --- add new lead
    st.subheader("Add a lead")
    with st.form("new_lead", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name*", placeholder="Jane Doe")
        email = c2.text_input("Email", placeholder="jane@example.com")
        company = c1.text_input("Company / Org", placeholder="Acme Ltd")
        source = c2.selectbox("Source", SOURCE_CHOICES, index=0)
        status = c1.selectbox("Status", STATUS_CHOICES, index=0)
        notes = st.text_area("Notes", placeholder="Context, next steps, etc.")
        submitted = st.form_submit_button("Add lead")

    if submitted:
        if not name.strip() and not email.strip():
            st.error("Please add at least a Name or an Email.")
        else:
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
            st.success(f"Added: {row['name'] or row['email'] or '(no name)'}")

    # --- filters
    with st.expander("Filters", expanded=True):
        q = st.text_input("Search (name, email, company, notes)")
        status_filter = st.multiselect("Status", STATUS_CHOICES, default=STATUS_CHOICES)
        src_values = sorted([s for s in df["source"].dropna().unique().tolist() if s])
        source_filter = st.multiselect("Source", src_values, default=src_values)
        if st.button("Reset filters"):
            st.rerun()

    filtered = df.copy()
    if q:
        ql = q.lower()
        filtered = filtered[
            filtered.apply(
                lambda r: ql in " ".join(str(r[c]) for c in ["name", "email", "company", "notes"]).lower(),
                axis=1,
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

    # --- csv actions
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
            st.success(f"Imported {len(add_df)} rows.")
        except Exception as e:
            st.error(f"Import failed: {e}")

    # --- quick update
    if not df.empty:
        st.subheader("Quick Update")
        options = list(filtered.index)
        if options:
            labels = [f"{i}: {filtered.loc[i, 'name']}  [{filtered.loc[i, 'status']}]" for i in options]
            pick = st.selectbox("Pick a row", options, format_func=lambda i: labels[options.index(i)])
            new_status = st.selectbox("New status", STATUS_CHOICES)
            c1, c2 = st.columns(2)
            if c1.button("Update status"):
                df.loc[pick, "status"] = new_status
                _save_df(df)
                st.success("Status updated!")
            if c2.button("Delete selected row"):
                df = df.drop(index=pick).reset_index(drop=True)
                _save_df(df)
                st.success("Row deleted.")

    st.caption("If the page was blank earlier, the blue DEBUG lines above prove the app is running.")


if __name__ == "__main__":
    app()
