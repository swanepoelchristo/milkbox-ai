import streamlit as st
from components.doc_locations import render_doc_locations_settings

def render():
    st.title("🧰 Milkbox AI Toolbox")
    st.subheader("Welcome")
    st.write("This is your central hub. Pick a tool on the left, or set the document locations below.")

    st.divider()
    with st.expander("🔗 Set Document Locations (admin)", expanded=False):
        render_doc_locations_settings()

    st.caption("Tools resolve URLs in priority: Secrets → locations.yaml → inline config.")
