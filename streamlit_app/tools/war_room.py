import os
import base64
from datetime import datetime
import streamlit as st

# This War Room tool saves “plans” into war_room/plans/ as YAML text.
# Right now it just creates the file content locally (via GitHub API later).

def render():
    st.title("⚔️ War Room")
    st.caption("Draft new ideas. Milkbot will turn them into plans.")

    with st.form("war_room_form", clear_on_submit=False):
        title = st.text_input("Plan title", placeholder="e.g. Food Safety Stub")
        description = st.text_area("Description", height=120, placeholder="What do you want Milkbot to build?")
        submitted = st.form_submit_button("Save Plan")

    if not submitted:
        return

    if not title.strip():
        st.error("Please enter a plan title.")
        return

    # Create a simple filename
    safe_title = "".join(ch for ch in title.lower().replace(" ", "_") if ch.isalnum() or ch in ("_", "-"))
    fname = f"{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{safe_title}.yaml"

    # Build YAML-like text
    plan = f"""# War Room Plan
title: {title}
created: {datetime.utcnow().isoformat()}Z
description: |
  {description or "(no description)"}
status: draft
"""

    # Show to user
    st.success(f"✅ Plan prepared: war_room/plans/{fname}")
    st.code(plan, language="yaml")
    st.download_button("⬇️ Download plan file", plan.encode("utf-8"), file_name=fname, mime="text/yaml")

    st.info("Next step: Milkbot will learn to push this file into GitHub (branch) automatically.")
