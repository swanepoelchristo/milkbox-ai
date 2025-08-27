import streamlit as st
import csv
import io
from datetime import datetime

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
CURRENCIES = {
    "USD ($)": "$",
    "ZAR (R)": "R",
    "EUR (€)": "€",
    "GBP (£)": "£",
}

def parse_items(text: str):
    """
    Parse text lines in the format:
      description | qty | price
    Returns (rows, errors, total)
    rows: list[dict] with keys: description, qty, price, line_total
    errors: list[str] warnings about skipped lines
    total: float grand total
    """
    rows = []
    errors = []
    total = 0.0

    for i, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3:
            errors.append(f"Line {i}: expected 3 fields (desc | qty | price), got {len(parts)} → '{raw}'")
            continue

        desc, qty_s, price_s = parts
        try:
            # Allow both int/float qty; price as float
            qty = float(qty_s)
            price = float(price_s)
        except ValueError:
            errors.append(f"Line {i}: qty and price must be numeric → '{raw}'")
            continue

        line_total = qty * price
        rows.append({
            "Description": desc,
            "Qty": qty,
            "Unit price": price,
            "Line total": line_total,
        })
        total += line_total

    return rows, errors, total


def csv_bytes(rows):
    """Return CSV bytes (utf-8) for rows (list of dicts)."""
    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return buf.getvalue().encode("utf-8")


# -------------------------------------------------------------------
# UI
# -------------------------------------------------------------------
def render():
    st.header("📄 Invoice Generator")

    # --- Left column: inputs
    with st.form("invoice_form", clear_on_submit=False):
        client_name = st.text_input("Client name", "")
        client_email = st.text_input("Client email", "")

        st.caption("Items (one per line, format: description | qty | price)")
        default_items = "Design work | 10 | 50\nHosting | 1 | 12.99"
        items_text = st.text_area(
            "Items",
            value=default_items,
            height=150,
            help="Each line: description | qty | price. Example: 'Design | 2 | 99.99'"
        )

        currency_label = st.selectbox(
            "Currency",
            options=list(CURRENCIES.keys()),
            index=0
        )
        submit = st.form_submit_button("Preview")

    # --- Right / below: preview
    if submit:
        rows, errors, total = parse_items(items_text)
        symbol = CURRENCIES[currency_label]

        # Client summary
        st.subheader("Client")
        if client_name or client_email:
            st.write(
                f"**Name:** {client_name or '—'}  \n"
                f"**Email:** {client_email or '—'}"
            )
        else:
            st.write("_No client details entered._")

        # Warnings
        if errors:
            with st.expander("⚠️ Skipped lines / warnings", expanded=False):
                for msg in errors:
                    st.warning(msg)

        # Items table
        st.subheader("Items")
        if rows:
            # Render currency formatting in a copy for display
            display_rows = []
            for r in rows:
                display_rows.append({
                    "Description": r["Description"],
                    "Qty": r["Qty"],
                    "Unit price": f"{symbol}{r['Unit price']:.2f}",
                    "Line total": f"{symbol}{r['Line total']:.2f}",
                })
            st.dataframe(display_rows, use_container_width=True, hide_index=True)

            # Total
            st.metric("Total", f"{symbol}{total:.2f}")

            # Download CSV
            csv_data = csv_bytes(rows)
            today = datetime.now().strftime("%Y-%m-%d")
            default_file = f"invoice_{today}.csv"
            st.download_button(
                "⬇️ Download CSV",
                data=csv_data,
                file_name=default_file,
                mime="text/csv",
            )
        else:
            st.info("No valid line items to display yet. Add lines and click **Preview**.")


# Allow running locally:  streamlit run streamlit_app/tools/invoice_gen.py
if __name__ == "__main__":
    render()
