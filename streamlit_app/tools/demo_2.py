import streamlit as st

def render():
    st.header("🧩 Demo Tool 2")
    st.write("New tool created by the Tool Builder.")

    with st.form("demo 2_form", clear_on_submit=False):
        example = st.text_input("Example input", value="")
        submitted = st.form_submit_button("Run")

    if submitted:
        st.success(f"✅ Demo Tool 2 ran successfully!")
