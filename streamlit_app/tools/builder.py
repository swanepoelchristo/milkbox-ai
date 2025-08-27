import os
import json
import base64
from datetime import datetime

import requests
import streamlit as st
import yaml

# ─────────────────────────────────────────────────────────
# Secrets / Config  (set in Streamlit Cloud → App → Settings → Secrets)
#   GITHUB_TOKEN (repo scope)
#   GITHUB_REPO  e.g. "swanepoelchristo/milkbox-ai"
#   GITHUB_BRANCH (optional, default "main")
# ─────────────────────────────────────────────────────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

API_ROOT = "https://api.github.com"
HDRS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────
def b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("utf-8")

def slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("-", "_").replace(" ", "_")
    return "".join(ch for ch in s if ch.isalnum() or ch == "_").strip("_")

def gh_get(path: str, params=None):
    return requests.get(f"{API_ROOT}{path}", headers=HDRS, params=params or {})

def gh_post(path: str, payload: dict):
    return requests.post(f"{API_ROOT}{path}", headers=HDRS, json=payload)

def gh_put(path: str, payload: dict):
    return requests.put(f"{API_ROOT}{path}", headers=HDRS, json=payload)

def gh_content_get(path: str, ref: str = None):
    params = {"ref": ref} if ref else None
    return gh_get(f"/repos/{GITHUB_REPO}/contents/{path}", params=params)

def gh_content_put(path: str, message: str, content_b64: str, branch: str, sha: str | None = None):
    payload = {"message": message, "content": content_b64, "branch": branch}
    if sha:
        payload["sha"] = sha
    return gh_put(f"/repos/{GITHUB_REPO}/contents/{path}", payload)

# ─────────────────────────────────────────────────────────
# YAML load/save for tools.yaml (root of the repo)
# ─────────────────────────────────────────────────────────
def fetch_yaml_from_main(path="tools.yaml"):
    r = gh_content_get(path, ref=GITHUB_BRANCH)
    if r.status_code == 404:
        # create an empty YAML structure the first time
        return {"tools": []}, None, None
    if r.status_code != 200:
        return None, None, f"Could not read {path}: {r.status_code} {r.text}"

    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    sha = data["sha"]
    try:
        y = yaml.safe_load(content) or {}
    except Exception as e:
        return None, None, f"YAML parse error in {path}: {e}"
    return y, sha, None

def ensure_tools_entry(ydata: dict, key: str, label: str):
    """Ensure the tools list contains this tool with a SAFE module path."""
    safe_key = slugify(key)
    ydata = ydata or {}
    tools = list(ydata.get("tools", []))
    if not any(isinstance(t, dict) and t.get("key") == safe_key for t in tools):
        tools.append({"key": safe_key, "label": label, "module": f"tools.{safe_key}"})
    ydata["tools"] = tools
    return ydata

def save_yaml_to_main(ydata: dict, sha: str | None, path="tools.yaml", message="chore: update tools.yaml"):
    text = yaml.safe_dump(ydata, sort_keys=False, allow_unicode=True)
    content_b64 = b64(text)
    return gh_content_put(path, message, content_b64, GITHUB_BRANCH, sha=sha)

# ─────────────────────────────────────────────────────────
# Tool file + spec file scaffolding
# ─────────────────────────────────────────────────────────
def generate_tool_py(safe_key: str, label: str, description: str) -> str:
    """Return a minimal Streamlit tool module with a render() entrypoint."""
    desc = (description or "New tool created by the Tool Builder.").replace('"', '\\"').strip()
    return f'''import streamlit as st

def render():
    st.header("🧩 {label}")
    st.write("{desc}")

    with st.form("{safe_key}_form", clear_on_submit=False):
        example = st.text_input("Example input", value="")
        submitted = st.form_submit_button("Run")

    if submitted:
        st.success(f"✅ {label} ran! You typed: {{example}}")
'''

def write_tool_file(tool_key: str, label: str, description: str):
    """Create the Python file for a new tool with a safe slugified filename."""
    safe_key = slugify(tool_key)
    code = generate_tool_py(safe_key, label, description)
    path = f"streamlit_app/tools/{safe_key}.py"
    msg = f"feat: add {label} tool"

    r = gh_content_put(path, msg, b64(code), GITHUB_BRANCH)
    if r.status_code not in (200, 201):
        return False, f"GitHub error {r.status_code}: {r.text}", None
    return True, f"✅ Created {path} for {label}", safe_key

def write_spec_file(safe_key: str, label: str, description: str):
    """Store a JSON spec that we (or CI) can use later to flesh out the tool."""
    spec = {
        "key": safe_key,
        "label": label,
        "description": description,
        "created": datetime.utcnow().isoformat() + "Z",
        "status": "draft",
    }
    spec_path = f"tool_specs/{safe_key}.json"
    msg = f"chore: add spec for {label}"
    r = gh_content_put(spec_path, msg, b64(json.dumps(spec, indent=2)), GITHUB_BRANCH)
    if r.status_code not in (200, 201):
        return False, f"GitHub error {r.status_code}: {r.text}", spec_path
    return True, f"📝 Wrote {spec_path}", spec_path

def open_issue_for_spec(spec_path: str, label: str, description: str):
    title = f"[Tool Spec] {label}"
    body = f"""A new tool spec was generated by the Tool Builder.

**Spec file:** `{spec_path}`

**Summary**
{description or ""}

Please implement the first working version using this spec, and link the PR here.
"""
    r = gh_post(f"/repos/{GITHUB_REPO}/issues", {"title": title, "body": body})
    return r

# ─────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────
def render():
    st.header("🛠️ Tool Builder")
    st.caption("This tool takes a name + description, creates a scaffold tool in GitHub, then registers it in `tools.yaml`.")

    if not GITHUB_TOKEN or not GITHUB_REPO:
        st.error("Missing GitHub secrets. Please set GITHUB_TOKEN and GITHUB_REPO in Streamlit Secrets.")
        with st.expander("Expected secrets"):
            st.code(
                "GITHUB_TOKEN = 'ghp_xxx'  # with repo scope\n"
                "GITHUB_REPO  = 'owner/repo'\n"
                "GITHUB_BRANCH = 'main'\n",
                language="toml",
            )
        return

    with st.form("builder_form", clear_on_submit=False):
        tool_key = st.text_input("Tool key (e.g. invoice_gen)")
        tool_label = st.text_input("Tool label (e.g. Invoice Generator)")
        description = st.text_area("Short description (what this tool should do)")

        submitted = st.form_submit_button("Generate tool")

    if not submitted:
        return

    if not tool_key or not tool_label:
        st.error("Please enter both a tool key and label.")
        return

    safe_key = slugify(tool_key)

    # 1) Write the tool .py file
    ok, msg, safe_key = write_tool_file(tool_key, tool_label, description)
    if ok:
        st.success(msg)
    else:
        st.error(msg)
        return

    # 2) Write the JSON spec
    ok2, msg2, spec_path = write_spec_file(safe_key, tool_label, description)
    if ok2:
        st.success(msg2)
    else:
        st.warning(msg2)

    # 3) Register in tools.yaml
    y, sha, err = fetch_yaml_from_main("tools.yaml")
    if err:
        st.error(err)
        return
    updated_yaml = ensure_tools_entry(y, safe_key, tool_label)
    r = save_yaml_to_main(updated_yaml, sha, path="tools.yaml", message=f"chore: register {tool_label} in tools.yaml")
    if r.status_code in (200, 201):
        st.success("📇 Registered the tool in tools.yaml. It should appear in the sidebar after reload.")
    else:
        st.error(f"GitHub error updating tools.yaml: {r.status_code} {r.text}")
        return

    # 4) Open an issue to track completion
    r_issue = open_issue_for_spec(spec_path, tool_label, description)
    if r_issue.status_code in (200, 201):
        st.info("🔗 Opened an Issue for this tool’s spec.")
    else:
        st.warning(f"Could not open issue automatically ({r_issue.status_code}). You can add it later.")
