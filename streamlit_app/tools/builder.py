import streamlit as st
import requests
import os

def render():
    st.header("🛠️ Tool Builder")
    st.write("This tool will take a name + description and create a scaffold tool in GitHub.")

    with st.form("builder_form"):
        tool_key = st.text_input("Tool key (e.g. invoice)")
        tool_label = st.text_input("Tool label (e.g. Invoice Generator)")
        description = st.text_area("Short description", "Write what this tool should do...")
        submitted = st.form_submit_button("Generate tool")

    if submitted:
        if not tool_key or not tool_label:
            st.error("Please fill in both key and label.")
            return

        # Build a simple Python scaffold
        code = f'''
import streamlit as st

def render():
    st.header("{tool_label}")
    st.write("This is the start of the {tool_label} tool.")
'''

        # GitHub API setup
        token = os.getenv("GITHUB_TOKEN")
        repo = os.getenv("GITHUB_REPO")
        branch = os.getenv("GITHUB_BRANCH", "main")

        if not token or not repo:
            st.error("Missing GitHub secrets in Streamlit Cloud.")
            return

        url = f"https://api.github.com/repos/{repo}/contents/streamlit_app/tools/{tool_key}.py"
        headers = {"Authorization": f"token {token}"}
        payload = {
            "message": f"feat: add {tool_key} tool",
            "content": code.encode("utf-8").decode("utf-8"),
            "branch": branch
        }

        # Send request
        r = requests.put(url, headers=headers, json=payload)

        if r.status_code in (200, 201):
            st.success(f"✅ Tool {tool_label} scaffold created in GitHub!")
            st.code(code, language="python")
            st.info("Remember to add it to tools.yaml to see it in the sidebar.")
        else:
            st.error(f"GitHub error: {r.status_code}")
            st.json(r.json())
