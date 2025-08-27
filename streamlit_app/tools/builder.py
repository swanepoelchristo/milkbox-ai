import os
import json
import base64
import requests
import streamlit as st

def render():
    st.header("🛠️ Tool Builder")
    st.write("This tool will take a name + description and create a scaffold tool in GitHub.")

    # --- Form inputs
    with st.form("builder_form", clear_on_submit=False):
        tool_key = st.text_input("Tool key (e.g. invoice)", placeholder="demo").strip()
        tool_label = st.text_input("Tool label (e.g. Invoice Generator)", placeholder="Demo Tool").strip()
        tool_description = st.text_area("Short description", placeholder="This is a test tool created by the Tool Builder.").strip()
        submitted = st.form_submit_button("Generate tool")

    if not submitted:
        return

    # --- Basic validation
    if not tool_key:
        st.error("Please enter a tool key.")
        return
    if not tool_label:
        st.error("Please enter a tool label.")
        return

    # --- Scaffold code that will be written to streamlit_app/tools/{tool_key}.py
    code = f'''import streamlit as st

def render():
    st.header("🧩 {tool_label}")
    st.write("{tool_description or "New tool created by the Tool Builder."}")

    with st.form("{tool_key}_form", clear_on_submit=False):
        example = st.text_input("Example input", value="")
        submitted = st.form_submit_button("Run")

    if submitted:
        st.success(f"✅ {tool_label} ran successfully!")
'''

    # --- GitHub API setup (secrets configured in Streamlit Cloud)
    token = os.getenv("GITHUB_TOKEN")          # ghp_xxx with 'repo' scope
    repo  = os.getenv("GITHUB_REPO")           # e.g. "swanepoelchristo/milkbox-ai"
    branch = os.getenv("GITHUB_BRANCH", "main")

    if not token or not repo:
        st.error("Missing GitHub secrets. Please set GITHUB_TOKEN and GITHUB_REPO in Streamlit ➜ App ➜ Settings ➜ Secrets.")
        return

    # --- Build the GitHub "Create or update file contents" request
    path_in_repo = f"streamlit_app/tools/{tool_key}.py"
    url = f"https://api.github.com/repos/{repo}/contents/{path_in_repo}"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    payload = {
        "message": f"feat(tools): add {tool_key} tool scaffold",
        "content": base64.b64encode(code.encode("utf-8")).decode("utf-8"),  # ✅ Base64
        "branch": branch,
    }

    # Try to PUT (create). If the file exists, fetch SHA and update.
    r = requests.put(url, headers=headers, json=payload)

    if r.status_code == 201:
        st.success(f"✅ Tool **{tool_key}** created at `{path_in_repo}`.")
        st.code(code, language="python")
        st.info("Add it to `tools.yaml` to see it in the sidebar.")
        return

    if r.status_code == 422:
        # Likely “already exists”. Fetch SHA, then update.
        get_r = requests.get(url, headers=headers, params={"ref": branch})
        if get_r.ok:
            sha = get_r.json().get("sha")
            if sha:
                payload["message"] = f"chore(tools): update {tool_key} tool scaffold"
                payload["sha"] = sha
                upd = requests.put(url, headers=headers, json=payload)
                if upd.ok:
                    st.success(f"♻️ Tool **{tool_key}** updated at `{path_in_repo}`.")
                    st.code(code, language="python")
                    st.info("Ensure it is registered in `tools.yaml`.")
                    return

        st.error("GitHub says the content is invalid or cannot be created/updated. See details below.")
        st.json(r.json())
        return

    # Any other error
    st.error(f"GitHub error: {r.status_code}")
    try:
        st.json(r.json())
    except Exception:
        st.write(r.text)

