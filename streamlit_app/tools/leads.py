# streamlit_app/tools/leads.py
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import os, re, sqlite3
import streamlit as st

# Optional .env (safe if not installed)
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

# Lazy imports so CI can import without heavy deps
try:
    import pandas as pd  # type: ignore
except Exception:
    pd = None  # type: ignore

try:
    from supabase import create_client  # type: ignore
except Exception:
    create_client = None  # type: ignore

# Reusable About/How-to block (fallback if helper missing)
try:
    from streamlit_app.tools._common import about  # type: ignore
except Exception:
    def about(description: str, howto_md: str, deps_cmd: str | None = None, notes: str | None = None):
        with st.expander("About / How to", expanded=False):
            st.markdown(description)
            st.markdown("**How to use**")
            st.markdown(howto_md)
            if deps_cmd:
                st.markdown("**Install (local)**")
                st.code(deps_cmd, language="bash")
            if notes:
                st.info(notes)

DATA_DIR = Path("data")
CSV_FILE = DATA_DIR / "leads.csv"
SQLITE_FILE = DATA_DIR / "leads.db"
SQLITE_TABLE = "leads"
SUPABASE_TABLE = "leads"

COLUMNS = ["created_at", "name", "email", "company", "source", "status", "notes"]
STATUS_CHOICES = ["New", "Contacted", "Qualified", "Won", "Lost"]
SOURCE_CHOICES = ["Website", "Referral", "LinkedIn", "Inbound", "Outbound", "Event", "Other"]

# ---------- utils ----------
def _valid_email(s: str) -> bool:
    if not s:
        return True
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", s.strip()))

def _empty_df():
    assert pd is not None, "pandas required at runtime"
    return pd.DataFrame(columns=COLUMNS)  # type: ignore[attr-defined]

def _ensure_schema(df):
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = ""
    return df[[c for c in COLUMNS if c in df.columns]]

# ---------- CSV ----------
def _load_df_csv():
    assert pd is not None, "pandas required at runtime"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CSV_FILE.exists():
        return _empty_df()
    try:
        df = pd.read_csv(CSV_FILE)  # type: ignore[attr-defined]
    except Exception as e:
        st.error(f"Couldn't read {CSV_FILE}: {e}")
        st.info("Close it in Excel if open. Starting empty.")
        return _empty_df()
    return _ensure_schema(df)

def _save_df_csv(df):
    try:
        df.to_csv(CSV_FILE, index=False)  # type: ignore[attr-defined]
        st.toast(f"Saved to {CSV_FILE}", icon="✅")
    except PermissionError:
        st.error("Save failed: CSV locked by another program (Excel). Close it and click **Retry save**.")
    except Exception as e:
        st.error(f"Save failed: {e}")

# ---------- SQLite ----------
def _init_sqlite():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(SQLITE_FILE))
    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SQLITE_TABLE} (
            created_at TEXT, name TEXT, email TEXT UNIQUE, company TEXT,
            source TEXT, status TEXT, notes TEXT
        )
        """
    )
    return con

def _load_df_sqlite():
    assert pd is not None, "pandas required at runtime"
    con = _init_sqlite()
    try:
        df = pd.read_sql_query(f"SELECT * FROM {SQLITE_TABLE}", con)  # type: ignore[attr-defined]
    finally:
        con.close()
    return _ensure_schema(df)

def _save_df_sqlite(df):
    con = _init_sqlite()
    try:
        con.execute(f"DELETE FROM {SQLITE_TABLE}")
        con.commit()
        df.to_sql(SQLITE_TABLE, con, if_exists="append", index=False)  # type: ignore[attr-defined]
        st.toast(f"Saved to {SQLITE_FILE}", icon="✅")
    except Exception as e:
        st.error(f"Save failed: {e}")
    finally:
        con.close()

# ---------- Supabase ----------
def _get_supabase_client():
    url = os.environ.get("SUPABASE_URL")
    key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or os.environ.get("SUPABASE_KEY")
        or os.environ.get("SUPABASE_ANON_KEY")
    )
    if create_client is None:
        return None, 'Install client: pip install "supabase>=2,<3"'
    if not url or not key:
        return None, "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in your environment."
    try:
        return create_client(url, key), None
    except Exception as e:
        return None, f"Could not create Supabase client: {e}"

def _load_df_supabase():
    assert pd is not None, "pandas required at runtime"
    client, err = _get_supabase_client()
    if err:
        st.warning(err)
        return _empty_df()
    try:
        res = client.table(SUPABASE_TABLE).select("*").execute()
        df = pd.DataFrame(res.data or [])  # type: ignore[attr-defined]
        return _ensure_schema(df)
    except Exception as e:
        st.error(f"Failed to load from Supabase: {e}")
        return _empty_df()

def _save_df_supabase(df):
    client, err = _get_supabase_client()
    if err:
        st.error(err)
        return
    try:
        up = df.copy()
        if "email" in up.columns:
            up["email"] = up["email"].astype(str).str.strip().str.lower()
        payload = up[COLUMNS].to_dict(orient="records")  # type: ignore[attr-defined]
        client.table(SUPABASE_TABLE).upsert(payload, on_conflict="email").execute()
        st.toast("Saved to Supabase", icon="✅")
    except Exception as e:
        st.error(f"Failed to save to Supabase: {e}")

# ---------- UI ----------
def app():
    st.title("Leads Tracker")
    about(
        description="Mini CRM for capturing leads. Backends: **CSV** (default), **SQLite** (local), **Supabase** (cloud).",
        howto_md=(
            "1. Fill **Add a lead** → **Add lead**.  \n"
            "2. Use **Filters** to search.  \n"
            "3. Edit inline in the table → **Apply edited changes**.  \n"
            "4. **Settings**: choose backend & duplicate handling.  \n"
            "5. **Download** CSV / **Upload** CSV / use **Retry save** if the CSV was locked."
        ),
        deps_cmd='pip install streamlit pandas "supabase>=2,<3" python-dotenv',
        notes="Local files live in `data/` and are ignored by git. Supabase table name: `leads`.",
    )

    if pd is None:
        st.warning("This tool needs **pandas**. Install and refresh:\n\n```bash\npip install pandas\n```")
        return

    # Settings
    with st.expander("Settings", expanded=False):
        backend_label = st.selectbox(
            "Storage backend", ["CSV (local)", "SQLite (local)", "Supabase (cloud)"], key="leads_backend"
        )
        dup_mode = st.radio(
            "When a duplicate email is added",
            ["Update existing by email", "Allow duplicate row"],
            horizontal=True,
            key="dup_mode",
        )
        require_valid = st.checkbox("Require valid email format", value=True, key="require_valid_email")
        if backend_label.startswith("Supabase"):
            if st.button("Test Supabase connection"):
                client, err = _get_supabase_client()
                st.success("Connected!") if client and not err else st.error(err or "Unknown error")

    # Choose backend
    if backend_label.startswith("CSV"):
        load_df, save_df = _load_df_csv, _save_df_csv
    elif backend_label.startswith("SQLite"):
        load_df, save_df = _load_df_sqlite, _save_df_sqlite
    else:
        load_df, save_df = _load_df_supabase, _save_df_supabase

    df = _ensure_schema(load_df())

    # Add lead
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
        elif require_valid and not _valid_email(email.strip()):
            st.error("Email looks invalid.")
        else:
            row = {
                "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "name": name.strip(),
                "email": email.strip().lower(),
                "company": company.strip(),
                "source": source,
                "status": status,
                "notes": notes.strip(),
            }
            if row["email"]:
                mask = df["email"].astype(str).str.lower() == row["email"]
                if mask.any() and st.session_state.get("dup_mode") == "Update existing by email":
                    idx = df[mask].index[0]
                    for k in ["name", "company", "source", "status", "notes"]:
                        df.loc[idx, k] = row[k]
                    st.info("Updated existing lead by email.")
                else:
                    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)  # type: ignore[attr-defined]
                    st.success(f"Added: {row['name'] or row['email'] or '(no name)'}")
            else:
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)  # type: ignore[attr-defined]
                st.success(f"Added: {row['name'] or '(no name)'}")
            df = _ensure_schema(df)
            save_df(df)

    # Filters
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
                lambda r: ql in " ".join(str(r[c]) for c in ["name", "email", "company", "notes"]).lower(), axis=1
            )
        ]
    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]
    if source_filter:
        filtered = filtered[filtered["source"].isin(source_filter)]

    # Table + inline edit
    st.subheader(f"Leads ({len(filtered)})")
    if filtered.empty:
        st.info("No rows match your filters.")
    edited = st.data_editor(
        filtered, key="leads_editor", width="stretch", height=350, num_rows="fixed"
    )
    if st.button("Apply edited changes"):
        for idx in edited.index:
            for col in COLUMNS:
                if col in edited.columns:
                    df.loc[idx, col] = edited.loc[idx, col]
        df = _ensure_schema(df)
        save_df(df)
        st.success("Edits saved.")

    # Quick update
    if not filtered.empty:
        with st.expander("Quick Update"):
            options = list(filtered.index)
            labels = [f"{i}: {filtered.loc[i,'name']} [{filtered.loc[i,'status']}]"] if options else []
            pick = st.selectbox(
                "Pick a row",
                options,
                format_func=lambda i: labels[options.index(i)] if options else str(i),
            )
            new_status = st.selectbox("New status", STATUS_CHOICES)
            c1, c2 = st.columns(2)
            if c1.button("Update status"):
                df.loc[pick, "status"] = new_status
                save_df(df)
                st.success("Status updated!")
            if c2.button("Delete selected row"):
                df = df.drop(index=pick).reset_index(drop=True)
                save_df(df)
                st.success("Row deleted.")

    # CSV export/import
    st.write("### CSV export/import")
    if pd is not None:
        csv_bytes = filtered.to_csv(index=False).encode("utf-8")  # type: ignore[attr-defined]
        st.download_button("Download filtered CSV", csv_bytes, "leads.csv", "text/csv")
    uploaded = st.file_uploader("Optional: upload a leads CSV to append", type=["csv"])
    if uploaded is not None and pd is not None:
        try:
            add_df = pd.read_csv(uploaded)  # type: ignore[attr-defined]
            add_df = _ensure_schema(add_df)
            df = pd.concat([df, add_df], ignore_index=True)  # type: ignore[attr-defined]
            df = _ensure_schema(df)
            save_df(df)
            st.success(f"Imported {len(add_df)} rows.")
        except Exception as e:
            st.error(f"Import failed: {e}")

    # Retry save
    if st.button("Retry save"):
        save_df(df)

    st.caption("Backends: CSV / SQLite / Supabase. Local data in `data/` is ignored by git.")

if __name__ == "__main__":
    app()
