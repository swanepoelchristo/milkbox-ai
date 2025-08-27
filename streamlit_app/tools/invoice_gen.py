import streamlit as st
import pandas as pd

def render():
    st.header("🧾 Invoice Generator")

    with st.form("invoice_form", clear_on_submit=False):
        client = st.text_input("Client name")
        email = st.text_input("Client email")
        items = st.text_area(
            "Items (one per line, format: description | qty | price)",
            placeholder="Design work | 10 | 50\nHosting | 1 | 12.99"
        )
        submitted = st.form_submit_button("Preview")

    if submitted:
        rows = []
        total = 0.0

        for raw in items.splitlines():
            if not raw.strip():
                continue
            parts = [p.strip() for p in raw.split("|")]
            if len(parts) < 3:
                st.warning(f"Skipping malformed line: {raw}")
                continue

            desc, qty_s, price_s = parts[0], parts[1], parts[2]
            try:
                qty = float(qty_s)
                price = float(price_s)
                amount = qty * price
            except ValueError:
                st.warning(f"Skipping line with non-numeric qty/price: {raw}")
                continue

            rows.append({"Description": desc, "Qty": qty, "Price": price, "Amount": amount})
            total += amount

        st.subheader("Preview")
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
        st.metric("Total", f"{total:,.2f}")
        st.caption("Export to PDF/DOCX can be added later.")
