# streamlit_app/components/doc_locations.py
from __future__ import annotations
import yaml
from pathlib import Path
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
LOC_YAML = REPO_ROOT / "standards" / "locations.yaml"

SCHEMA_KEYS = [
    ("DOC_ISO22000_URL", "ISO 22000 (official/public URL)"),
    ("DOC_HACCP_URL", "Codex HACCP (official/public URL)"),
    ("DOC_LOCAL_REG_URL", "Local/National Regulation URL"),
    ("DOC_SOP_INDEX_URL", "Company SOP Index (SharePoint/Drive)"),
]

def _load_locations() -> dict:
    if LOC_YAML.exists():
        try:
            return yaml.safe_load(LOC_YAML.read_text(encoding="utf-8")) or {}
        except Exception:
            pass
    return {}

def _save_locations(data: dict) -> None:
    LOC_YAML.parent.mkdir(parents=True, exist_ok=True)
    LOC_YAML.write_text(yaml.safe_dump(data, sort_keys=True, allow_unicode=True), encoding="utf-8")

def render_doc_locations_settings():
    """
    Render a simple admin form to set document URLs.
    Priority elsewhere: st.secrets[...] > locations.yaml > others
    """
    st.subheader("🔗 Set Document Locations")
    st.caption(
        "Paste the permanent links where your standards and SOP index live. "
        "These are typically SharePoint / OneDrive / Google Drive / public standards pages. "
        "Saved to standards/locations.yaml (you can version-control it)."
    )

    existing = _load_locations()
    with st.form("doc_locations_form", clear_on_submit=False):
        inputs = {}
        for key, label in SCHEMA_KEYS:
            default = st.secrets.get(key, "") or existing.get(key, "")
            inputs[key] = st.text_input(label, value=default, key=f"loc_{key}")
        submitted = st.form_submit_button("💾 Save locations")

    if submitted:
        new_data = {}
        # Do not overwrite non-empty secrets; show what will be stored.
        for key, _ in SCHEMA_KEYS:
            val = inputs.get(key, "").strip()
            if val:
                new_data[key] = val
        _save_locations(new_data)
        st.success("Saved! (standards/locations.yaml)")
        st.caption("Note: If a Secret is set with the same key, that secret will still take priority at runtime.")

    with st.expander("📄 Current locations.yaml", expanded=False):
        if LOC_YAML.exists():
            st.code(LOC_YAML.read_text(encoding="utf-8"), language="yaml")
        else:
            st.info("No locations.yaml saved yet.")
