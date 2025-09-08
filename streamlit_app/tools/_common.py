from __future__ import annotations
import streamlit as st

def about(description: str, howto_md: str, deps_cmd: str | None = None, notes: str | None = None):
    """Reusable About/How-to block for Streamlit tools."""
    with st.expander("About / How to", expanded=False):
        st.markdown(description)
        st.markdown("**How to use**")
        st.markdown(howto_md)
        if deps_cmd:
            st.markdown("**Install (local)**")
            st.code(deps_cmd, language="bash")
        if notes:
            st.info(notes)
