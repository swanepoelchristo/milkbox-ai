import streamlit as st

def render():
    st.header("🧩 Invoice Generator")
    st.write("This tool takes user inputs for client, items, and prices, then generates a professional invoice PDF or DOCX.
")

    with st.form("invoice_gen_form", clear_on_submit=False):
        example = st.text_input("Example input", value="")
        submitted = st.form_submit_button("Run")

    if submitted:
        st.success(f"✅ Invoice Generator ran! You typed: {example}")