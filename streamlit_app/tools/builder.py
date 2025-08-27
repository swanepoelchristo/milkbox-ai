def generate_tool_py(key: str, label: str, description: str) -> str:
    """
    Return a complete Streamlit tool module (as code text) for the requested tool.
    - If the key/label/description suggests a known preset (invoice, cv/resume, notes, bar/menu),
      we return a richer scaffold for that preset.
    - Otherwise we return a simple, generic working stub.
    """
    norm = f"{key} {label} {description}".lower()

    def is_any(substrings: list[str]) -> bool:
        return any(s in norm for s in substrings)

    # ──────────────────────────────────────────────────────────────────
    # 1) Invoice Generator (rich preset)
    #    Keywords: invoice
    # ──────────────────────────────────────────────────────────────────
    if is_any(["invoice"]):
        return f'''import streamlit as st
from datetime import date

def render():
    st.header("🧾 {label}")
    st.caption("This is a starter scaffold created by the Tool Builder. Customize freely!")

    # ── Inputs
    st.subheader("Client")
    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input("Client name", value="Acme Corp")
        client_email = st.text_input("Client email", value="billing@acme.com")
    with col2:
        invoice_no = st.text_input("Invoice #", value="INV-0001")
        invoice_date = st.date_input("Invoice date", value=date.today())

    st.subheader("Your Business")
    your_name = st.text_input("Your name / business", value="Milkbox AI")
    your_email = st.text_input("Your email", value="invoices@milkbox.ai")

    st.subheader("Line items")
    items = st.session_state.setdefault("invoice_items", [
        {{"description": "Discovery workshop", "qty": 1, "unit_price": 1200.0}},
        {{"description": "Prototype", "qty": 1, "unit_price": 2400.0}},
    ])

    # Editable table-like UI
    for i, it in enumerate(items):
        c1, c2, c3, c4 = st.columns([4, 1, 2, 1])
        it["description"] = c1.text_input(f"Description #{i+1}", value=it["description"], key=f"desc_{i}")
        it["qty"] = c2.number_input(f"Qty #{i+1}", min_value=0, value=int(it["qty"]), key=f"qty_{i}")
        it["unit_price"] = c3.number_input(f"Unit price #{i+1}", min_value=0.0, value=float(it["unit_price"]), step=0.01, key=f"price_{i}")
        if c4.button("✖", key=f"del_{i}"):
            items.pop(i)
            st.experimental_rerun()

    if st.button("➕ Add line"):
        items.append({{"description": "", "qty": 1, "unit_price": 0.0}})
        st.experimental_rerun()

    subtotal = sum(float(it["qty"]) * float(it["unit_price"]) for it in items)
    tax_rate = st.number_input("Tax %", value=0.0, step=0.5)
    tax_amount = subtotal * (tax_rate / 100.0)
    total = subtotal + tax_amount

    st.subheader("Totals")
    c1, c2, c3 = st.columns(3)
    c1.metric("Subtotal", f"${{subtotal:,.2f}}")
    c2.metric("Tax", f"${{tax_amount:,.2f}}")
    c3.metric("Total", f"${{total:,.2f}}")

    st.divider()
    st.write("💡 **Next**: export to PDF/DOCX, brand it, and email it. (Add libs like `reportlab` or `python-docx`.)")

    if st.button("Simulate export"):
        st.success("Invoice export placeholder – wire up PDF/DOCX next!")
'''

    # ──────────────────────────────────────────────────────────────────
    # 2) CV / Resume Builder (preset)
    #    Keywords: cv, resume
    # ──────────────────────────────────────────────────────────────────
    if is_any(["cv", "resume"]):
        return f'''import streamlit as st

def render():
    st.header("📄 {label}")
    st.caption("Starter CV/Resume builder scaffold.")

    name = st.text_input("Full name", value="Jane Doe")
    email = st.text_input("Email", value="jane@example.com")
    role = st.text_input("Desired role", value="Product Manager")
    summary = st.text_area("Professional summary", height=120)

    st.subheader("Experience")
    exp = st.session_state.setdefault("cv_exp", [
        {{"title": "PM", "company": "Milkbox", "years": "2023–2025", "achievements": "- Led X\\n- Shipped Y"}}
    ])

    for i, e in enumerate(exp):
        with st.expander(f"Experience #{i+1}: " + (e.get("company") or "")):
            e["title"] = st.text_input("Title", value=e["title"], key=f"xt{i}")
            e["company"] = st.text_input("Company", value=e["company"], key=f"xc{i}")
            e["years"] = st.text_input("Years", value=e["years"], key=f"xy{i}")
            e["achievements"] = st.text_area("Achievements (bullets)", value=e["achievements"], key=f"xa{i}")
            if st.button("Remove", key=f"rm{i}"):
                exp.pop(i); st.experimental_rerun()

    if st.button("➕ Add experience"):
        exp.append({{"title": "", "company": "", "years": "", "achievements": ""}})
        st.experimental_rerun()

    st.divider()
    if st.button("Generate preview"):
        st.success("Preview ready (placeholder). Add export to DOCX/PDF next.")
'''

    # ──────────────────────────────────────────────────────────────────
    # 3) Notes (preset)
    #    Keywords: notes, note
    # ──────────────────────────────────────────────────────────────────
    if is_any(["notes", "note"]):
        return f'''import streamlit as st

def render():
    st.header("🗒️ {label}")
    st.caption("Simple notes workspace (session only). Extend to persist in GitHub/DB.")

    text = st.text_area("Write notes", height=220)
    if st.button("Save note"):
        st.session_state.setdefault("notes_list", []).append(text)
        st.success("Saved to session_state.")

    st.subheader("Saved (session)")
    for i, n in enumerate(st.session_state.get("notes_list", [])):
        st.markdown(f"- {{n[:80]}}…")
'''

    # ──────────────────────────────────────────────────────────────────
    # 4) Bar Menu / Bar Tools (preset)
    #    Keywords: bar, menu, cocktail, drink
    # ──────────────────────────────────────────────────────────────────
    if is_any(["bar", "menu", "cocktail", "drink"]):
        return f'''import streamlit as st

def render():
    st.header("🍸 {label}")
    st.caption("Starter for a bar/cocktail menu generator.")

    venue = st.text_input("Venue name", value="Milkbox Bar")
    theme = st.text_input("Menu theme", value="Tropical")
    items = st.session_state.setdefault("bar_items", [
        {{"name": "Sunset Mule", "ingredients": "Vodka, Lime, Ginger beer", "price": 11.0}}
    ])

    for i, it in enumerate(items):
        c1, c2, c3, c4 = st.columns([2, 4, 1, 1])
        it["name"] = c1.text_input("Name", value=it["name"], key=f"bn{i}")
        it["ingredients"] = c2.text_input("Ingredients", value=it["ingredients"], key=f"bi{i}")
        it["price"] = c3.number_input("Price", min_value=0.0, value=float(it["price"]), step=0.5, key=f"bp{i}")
        if c4.button("✖", key=f"bd{i}"):
            items.pop(i); st.experimental_rerun()

    if st.button("➕ Add item"):
        items.append({{"name": "", "ingredients": "", "price": 0.0}})
        st.experimental_rerun()

    st.divider()
    if st.button("Generate menu preview"):
        st.success("Menu preview (placeholder). Add PDF export/branding next.")
'''

    # ──────────────────────────────────────────────────────────────────
    # 5) Generic stub (fallback for any new idea)
    # ──────────────────────────────────────────────────────────────────
    # Always returns a working Streamlit module with a form.
    clean_desc = (description or "New tool created by the Tool Builder.").replace('"', '\\"')
    return f'''import streamlit as st

def render():
    st.header("🧩 {label}")
    st.write("{clean_desc}".strip())

    with st.form("{slugify(key)}_form", clear_on_submit=False):
        example = st.text_input("Example input", value="")
        submitted = st.form_submit_button("Run")

    if submitted:
        st.success(f"✅ {label} ran! You typed: {{example}}")
'''

