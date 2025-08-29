import streamlit as st

def _link_row(label: str, url_key: str, secret_key: str) -> None:
    """
    Shows a single row with:
      • auto-filled from st.secrets[secret_key] if present
      • else allow a manual URL
    Never crashes if missing.
    """
    col1, col2 = st.columns([1.3, 3])
    with col1:
        st.markdown(f"**{label}**")
        if st.secrets.get(secret_key):
            st.caption(f"from secret `{secret_key}`")
        else:
            st.caption("manual URL (no secret set)")

    with col2:
        default = st.secrets.get(secret_key, "")
        url = st.text_input(
            f"{label} URL",
            value=default,
            key=f"ql_{secret_key}",
            label_visibility="collapsed",
            placeholder=f"https://example.com/{url_key}",
        )
        if url:
            st.link_button("Open", url, use_container_width=False)


def render_quick_links_docs() -> None:
    with st.expander("▶ Quick access — Documents & SOPs", expanded=False):
        st.caption("Paste public links here or add them as secrets for auto-fill and reuse.")
        _link_row("ISO 22000 (Food Safety Management)", "iso22000", "DOC_ISO22000_URL")
        _link_row("Codex HACCP — General Principles", "haccp", "DOC_HACCP_URL")
        _link_row("Local/National Food Safety Regulation", "local_reg", "DOC_LOCAL_REG_URL")
        _link_row("Company SOP Index (SharePoint/Drive)", "sop_index", "DOC_SOP_INDEX_URL")
