import os
import json
import base64
from datetime import datetime

import requests
import streamlit as st
import yaml

# ─────────────────────────────────────────────────────────
# Secrets / Config (set in Streamlit Cloud → App → Settings → Secrets)
# Required: GITHUB_TOKEN, GITHUB_REPO
# Optional: GITHUB_BRANCH (defaults to "main")
# ─────────────────────────────────────────────────────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")          # e.g. "swanepoelchristo/milkbox-ai"
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
    s = s.strip().lower().replace(" ", "_").replace("-", "_")
    return "".join(ch for ch in s if (ch.isalnum() or ch == "_")).strip("_")


def gh_get(path: str, params=None):
    return requests.get(f"{API_ROOT}{path}", headers=HDRS, params=params or {})


def gh_put(path: str, payload: dict):
    return requests.put(f"{API_ROOT}{path}", headers=HDRS, json=payload)


def gh_content_get(path: str, ref: str = None):
    params = {"ref": ref} if ref else None
    return gh_get(f"/repos/{GITHUB_REPO}/contents/{path}", params=params)


def gh_content_put_update(path: str, message: str, content_str: str, branch: str):
    """
    Create or update a file in GitHub. If the file exists, include its SHA for update.
    This prevents 422: 'sha wasn't supplied' on updates.
    """
    sha = None
    existing = gh_content_get(path, ref=branch)
    if existing.status_code == 200:
        try:
            sha = existing.json().get("sha")
        except Exception:
            sha = None

    payload = {
        "message": message,
        "content": b64(content_str),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha

    return gh_put(f"/repos/{GITHUB_REPO}/contents/{path}", payload)


def load_yaml_from_repo(path: str, branch: str):
    r = gh_content_get(path, ref=branch)
    if r.status_code == 200:
        data = r.json()
        text = base64.b64decode(data["content"]).decode("utf-8")
        sha = data.get("sha")
        try:
            y = yaml.safe_load(text) or {}
        except Exception as e:
            return None, None, f"YAML parse error in {path}: {e}"
        return y, sha, None
    elif r.status_code == 404:
        # Not found — start from empty
        return {}, None, None
    else:
        return None, None, f"Could not read {path}: {r.status_code} {r.text}"


def ensure_tools_entry(ydata: dict, key: str, label: str):
    """
    Ensure tools.yaml contains (or updates) an entry for this tool.
    Structure:
      tools:
        - key: <key>
          label: <label>
          module: tools.<key>
    """
    ydata = ydata or {}
    tools = ydata.get("tools", [])
    found = False
    for t in tools:
        if isinstance(t, dict) and t.get("key") == key:
            t["label"] = label
            t["module"] = f"tools.{key}"
            found = True
            break
    if not found:
        tools.append({"key": key, "label": label, "module": f"tools.{key}"})
    ydata["tools"] = tools
    return ydata


def generate_tool_py(key: str, label: str, description: str) -> str:
    desc = (description or "New tool created by the Tool Builder.").replace('"', '\\"')
    return f'''import streamlit as st

def render():
    st.header("🧩 {label}")
    st.write("{desc}")

    with st.form("{key}_form", clear_on_submit=False):
        example = st.text_input("Example input", value="")
        submitted = st.form_submit_button("Run")

    if submitted:
        st.success(f"✅ {label} ran! You typed: {{example}}")
'''


# ─────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────
def render():
    st.header("🛠️ Tool Builder")

    if not (GITHUB_TOKEN and GITHUB_REPO):
        st.error("Missing GitHub secrets. Please set GITHUB_TOKEN and GITHUB_REPO in Streamlit Secrets.")
        return

    with st.form("builder_form", clear_on_submit=False):
        key_raw = st.text_input("Tool key (e.g. invoice_gen)", value="")
        label = st.text_input("Tool label (e.g. Invoice Generator)", value="")
        short_desc = st.text_area("Short description (what this tool should do)",
                                  value="", height=100)
        submitted = st.form_submit_button("Generate tool")

    if not submitted:
        return

    key = slugify(key_raw)
    if not key or not label:
        st.error("Tool key and label are required.")
        return

    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # 1) Write/update tool_specs/<key>.json (keeps a record of the brief)
    spec_path = f"tool_specs/{key}.json"
    spec_obj = {
        "key": key,
        "label": label,
        "description": short_desc,
        "created_at": ts,
        "source": "Tool Builder",
    }
    r_spec = gh_content_put_update(
        spec_path,
        message=f"chore(builder): write/update spec for {key}",
        content_str=json.dumps(spec_obj, indent=2) + "\n",
        branch=GITHUB_BRANCH,
    )
    if r_spec.status_code not in (200, 201):
        st.warning(f"Spec write warning ({r_spec.status_code}): {r_spec.text}")
    else:
        st.success(f"Wrote/updated {spec_path}")

    # 2) Write/update streamlit_app/tools/<key>.py (create scaffold or update existing)
    tool_code = generate_tool_py(key, label, short_desc)
    tool_py_path = f"streamlit_app/tools/{key}.py"
    r_tool = gh_content_put_update(
        tool_py_path,
        message=f"feat(builder): add/update tool {key}",
        content_str=tool_code,
        branch=GITHUB_BRANCH,
    )
    if r_tool.status_code not in (200, 201):
        st.error(f"GitHub error writing tool ({r_tool.status_code}): {r_tool.text}")
        return
    st.success(f"Created/updated {tool_py_path}")

    # 3) Read tools.yaml (create if missing), ensure entry, write/update
    ydata, _, err = load_yaml_from_repo("tools.yaml", GITHUB_BRANCH)
    if err:
        st.error(err)
        return

    ydata = ensure_tools_entry(ydata, key, label)
    yaml_text = yaml.safe_dump(ydata, sort_keys=False, allow_unicode=True)

    r_yaml = gh_content_put_update(
        "tools.yaml",
        message=f"chore(builder): register tool {key} in tools.yaml",
        content_str=yaml_text,
        branch=GITHUB_BRANCH,
    )
    if r_yaml.status_code not in (200, 201):
        st.error(f"GitHub error updating tools.yaml ({r_yaml.status_code}): {r_yaml.text}")
        return
    st.success("Registered the tool in tools.yaml. It should appear in the sidebar now.")

    st.code(tool_code, language="python")
