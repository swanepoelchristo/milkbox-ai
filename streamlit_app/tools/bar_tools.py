import streamlit as st

def render():
    st.header("🧩 Bar Tools (ABV & Tips)")
    st.write("Two quick helpers for bars: 1) ABV calculator (volume × ABV% → pure alcohol ml/g) and 2) Tip & bill split calculator. Keep it lightweight, fast, and mobile-friendly.
")

    with st.form("bar_tools_form", clear_on_submit=False):
        example = st.text_input("Example input", value="")
        submitted = st.form_submit_button("Run")

    if submitted:
        st.success(f"✅ Bar Tools (ABV & Tips) ran! You typed: {example}")
