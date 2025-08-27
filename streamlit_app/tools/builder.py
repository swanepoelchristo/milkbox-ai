import os
import json
import base64
import requests
import streamlit as st
import yaml  # PyYAML (already in requirements.txt)

GITHUB_API = "https://api.github.com"

def _gh_headers(token: str) -> dict:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

def _gh_get(repo: str, path: str, token: str, branch: str):
    """GET a file (contents API). Returns (status_code, json)."""
    url = f"{GITHUB_API}/repos/{repo}/contents/{path}"
    return requests.get(url, headers=_gh_headers(token), params={"ref": branch})

def _gh_put_file(repo: str, path: str, token: str, branch: str, content_b64: str, message: str, sha: str | None = None):
    """Create or update file via contents API."""
    url = f"{GITHUB_API}/repos/{repo}/contents/{path}"
    payload = {
        "message": message,
        "content": content_b64,
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha
    return requests.put(url, headers=_gh_headers(token), json=payload)

def _ensure_yaml_has_tool(yaml_text: str, tool_key: str, tool_label: str) -> tuple[str, bool]:
    """
    Returns (new_yaml_text, changed_flag). Keeps the existing format: 
    tools:
      - key: <key>
        label: <label>
        module: "tools.<key>"
    """
    data = yaml.safe_load(yaml_text) or {}
    if not isinstance(data, dict):
        data = {}

    tools = data.get("tools")
    if not isinstance(tools, list):
        tools = []
        data["tools"] = tools

    module_name = f"tools.{tool_key}"
    already = any(
        (isinstance(t, dict) and (t.get("key") == tool_key or t.get("module") == module_name))
        for t in tools
    )
    if already:
        return yaml.safe_dump(data, sort_keys=False), False

    tools.append({
        "key": tool_key,
        "label": tool_label,
        "module": module_name,
    })

    return yaml.safe_dump(data, sort_keys=False), True

def render():
    st.header("🛠️ Tool Builder")
    st.write("Give me a **key**, **label**, and optional **description** — I’ll scaffold a tool and register it in `tools.yaml` automatically.")

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

    # --- Scaffold code to be written into streamlit_app/tools/{tool_key}.py
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

    # --- GitHub configuration from Streamlit Secrets
    token  = os.getenv("GITHUB_TOKEN")          # ghp_xxx with 'repo' scope
    repo   = os.getenv("GITHUB_REPO")           # e.g. "swanepoelchristo/milkbox-ai"
    branch = os.getenv("GITHUB_BRANCH", "main")

    if not token or not repo:
        st.error("Missing GitHub secrets.\nSet **GITHUB_TOKEN** and **GITHUB_REPO** in Streamlit → App → Settings → Secrets.")
        return

    # 1) Create/update the tool file
    path_tool_py = f"streamlit_app/tools/{tool_key}.py"
    create_msg = f"feat(tools): add {tool_key} tool scaffold"
    update_msg = f"chore(tools): update {tool_key} tool scaffold"

    encoded = base64.b64encode(code.encode("utf-8")).decode("utf-8")

    # Try PUT (create)
    r = _gh_put_file(repo, path_tool_py, token, branch, encoded, create_msg)
    created = False

    if r.status_code == 201:
        created = True
        st.success(f"✅ Created `{path_tool_py}`")
    elif r.status_code == 422:
        # Probably exists — fetch SHA and update
        get_r = _gh_get(repo, path_tool_py, token, branch)
        if get_r.ok:
            sha = get_r.json().get("sha")
            upd = _gh_put_file(repo, path_tool_py, token, branch, encoded, update_msg, sha=sha)
            if upd.ok:
                st.success(f"♻️ Updated `{path_tool_py}`")
            else:
                st.error("GitHub update failed for tool file.")
                try:
                    st.json(upd.json())
                except Exception:
                    st.write(upd.text)
                return
        else:
            st.error("GitHub says the tool file exists but could not fetch SHA.")
            try:
                st.json(get_r.json())
            except Exception:
                st.write(get_r.text)
            return
    else:
        st.error(f"GitHub error creating tool file: {r.status_code}")
        try:
            st.json(r.json())
        except Exception:
            st.write(r.text)
        return

    st.code(code, language="python")

    # 2) Append to tools.yaml at repo root (so it appears in the sidebar)
    path_yaml = "tools.yaml"
    add_yaml_msg = f"chore(tools): register {tool_key} in tools.yaml"

    # Try fetch tools.yaml
    get_yaml = _gh_get(repo, path_yaml, token, branch)

    if get_yaml.status_code == 404:
        # Make a fresh YAML with just this tool
        base_yaml = "tools:\n"
        new_yaml_text, changed = _ensure_yaml_has_tool(base_yaml, tool_key, tool_label)
        yaml_b64 = base64.b64encode(new_yaml_text.encode("utf-8")).decode("utf-8")
        put_yaml = _gh_put_file(repo, path_yaml, token, branch, yaml_b64, add_yaml_msg)
        if put_yaml.ok:
            st.success("🧾 Created `tools.yaml` and registered the new tool.")
        else:
            st.warning("Created the Python file, but failed to create `tools.yaml`.")
            try:
                st.json(put_yaml.json())
            except Exception:
                st.write(put_yaml.text)
        return

    if not get_yaml.ok:
        st.warning("Tool file created/updated, but fetching `tools.yaml` failed.")
        try:
            st.json(get_yaml.json())
        except Exception:
            st.write(get_yaml.text)
        return

    # Decode, modify, re-upload
    yaml_json = get_yaml.json()
    current_sha = yaml_json.get("sha")
    yaml_text = base64.b64decode(yaml_json.get("content", "")).decode("utf-8", errors="ignore")

    new_yaml_text, changed = _ensure_yaml_has_tool(yaml_text, tool_key, tool_label)
    if not changed:
        st.info("ℹ️ `tools.yaml` already contains this tool. No changes made.")
        st.success("All done! Refresh the app if you don’t see it in the sidebar.")
        return

    yaml_b64 = base64.b64encode(new_yaml_text.encode("utf-8")).decode("utf-8")
    put_yaml = _gh_put_file(repo, path_yaml, token, branch, yaml_b64, add_yaml_msg, sha=current_sha)

    if put_yaml.ok:
        st.success("✅ Registered the tool in `tools.yaml`. It should appear in the sidebar now.")
    else:
        st.warning("Tool file created/updated, but updating `tools.yaml` failed.")
        try:
            st.json(put_yaml.json())
        except Exception:
            st.write(put_yaml.text)

