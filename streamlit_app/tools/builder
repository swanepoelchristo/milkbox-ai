import os
import base64
import json
from datetime import datetime

import requests
import streamlit as st
import yaml

# ─────────────────────────────────────────────────────────
# Config from Streamlit Secrets (set in Streamlit Cloud)
# ─────────────────────────────────────────────────────────
GITHUB_TOKEN  = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO   = os.getenv("GITHUB_REPO", "")          # e.g. "swanepoelchristo/milkbox-ai"
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
API_ROOT      = "https://api.github.com"

HDRS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


# ─────────────────────────────────────────────────────────
# GitHub helpers
# ─────────────────────────────────────────────────────────
def _gh_get(path: str, params=None):
    return requests.get(f"{API_ROOT}{path}", headers=HDRS, params=params or {})

def _gh_put(path: str, payload: dict):
    return requests.put(f"{API_ROOT}{path}", headers=HDRS, json=payload)

def _gh_post(path: str, payload: dict):
    return requests.post(f"{API_ROOT}{path}", headers=HDRS, json=payload)

def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")

def _read_file_and_sha(repo_path: str, ref: str = None):
    """Return (text_or_None, sha_or_None, err_or_None)"""
    r = _gh_get(f"/repos/{GITHUB_REPO}/contents/{repo_path}", params={"ref": ref} if ref else None)
    if r.status_code == 404:
        return None, None, None
    if r.status_code != 200:
        return None, None, f"GET {repo_path} failed: {r.status_code} {r.text}"
    data = r.json()
    try:
        text = base64.b64decode(data["content"]).decode("utf-8")
    except Exception as e:
        return None, None, f"decode error: {e}"
    return text, data.get("sha"), None

def _create_or_update_file(repo_path: str, content_text: str, commit_message: str):
    """
    Create or update a file using the correct sha (if present) so we *update* rather than overwrite.
    Returns (ok, message).
    """
    existing_text, sha, err = _read_file_and_sha(repo_path, ref=GITHUB_BRANCH)
    if err:
        return False, err

    payload = {
        "message": commit_message,
        "content": _b64(content_text),
        "branch": GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    r = _gh_put(f"/repos/{GITHUB_REPO}/contents/{repo_path}", payload)
    if r.status_code in (200, 201):
        return True, ("updated" if r.status_code == 200 else "created")
    # simple retry for race (optional: could re-fetch sha once)
    if r.status_code in (409, 422) and not sha:
        # try again by fetching sha
        existing_text, sha2, err2 = _read_file_and_sha(repo_path, ref=GITHUB_BRANCH)
        if err2:
            return False, err2
        payload["sha"] = sha2
        r2 = _gh_put(f"/repos/{GITHUB_REPO}/contents/{repo_path}", payload)
        if r2.status_code in (200, 201):
            return True, ("updated" if r2.status_code == 200 else "created")
        return False, f"PUT retry failed: {r2.status_code} {r2.text}"
    return False, f"PUT failed: {r.status_code} {r.text}"


# ─────────────────────────────────────────────────────────
# tools.yaml upsert (append or update, never wipe)
# ─────────────────────────────────────────────────────────
def upsert_tool_in_tools_yaml(tool_key: str, label: str, module_path: str) -> tuple[bool, str]:
    """
    Reads tools.yaml, merges/updates the entry for tool_key, and writes back using sha
    so existing entries remain intact. Returns (ok, message).
    """
    if not (GITHUB_TOKEN and GITHUB_REPO):
        return False, "Missing GITHUB_TOKEN or GITHUB_REPO."

    current_text, sha, err = _read_file_and_sha("tools.yaml", ref=GITHUB_BRANCH)
    if err:
        return False, err

    if current_text is None:
        data = {"tools": []}
    else:
        try:
            data = yaml.safe_load(current_text) or {}
        except Exception as e:
            return False, f"YAML parse error: {e}"

    tools = data.get("tools", [])
    found = False
    for t in tools:
        if isinstance(t, dict) and t.get("key") == tool_key:
            t["label"] = label
            t["module"] = module_path
            found = True
            break
    if not found:
        tools.append({"key": tool_key, "label": label, "module": module_path})

    data["tools"] = tools
    new_yaml = yaml.safe_dump(data, sort_keys=False, default_flow_style=False).rstrip() + "\n"

    payload = {
        "message": f"chore(builder): upsert tool '{tool_key}' into tools.yaml",
        "content": _b64(new_yaml),
        "branch": GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    r = _gh_put(f"/repos/{GITHUB_REPO}/contents/tools.yaml", payload)
    if r.status_code in (200, 201):
        return True, ("updated tools.yaml" if r.status_code == 200 else "created tools.yaml")
    return False, f"GitHub write failed: {r.status_code} {r.text}"


# ─────────────────────────────────────────────────────────
# Tool file scaffold
# ─────────────────────────────────────────────────────────
def make_tool_scaffold(tool_key: str, tool_label: str, description: str) -> str:
    """
    Minimal, clean Streamlit tool scaffold with a single form.
    """
    safe_desc = (description or "New tool created by the Tool Builder.").replace('"', '\\"')
    return f'''import streamlit as st

def render():
    st.header("🧩 {tool_label}")
    st.write("{safe_desc}")

    with st.form("{tool_key}_form", clear_on_submit=False):
        example = st.text_input("Example input", value="")
        submitted = st.form_submit_button("Run")

    if submitted:
        st.success(f"✅ {tool_label} ran! You typed: {{example}}")
'''


# ─────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────
def render():
    st.title("🛠️ Tool Builder")
    st.caption("Create or update a tool module in GitHub and auto-register it in tools.yaml (append/update, no duplicates).")

    if not GITHUB_TOKEN or not GITHUB_REPO:
        st.error("Missing `GITHUB_TOKEN` or `GITHUB_REPO` in Streamlit secrets. Please add them in Streamlit Cloud → App → Settings → Secrets.")
        return

    with st.form("builder_form", clear_on_submit=False):
        tool_key   = st.text_input("Tool key (e.g. invoice_gen, bar_tools)", value="")
        tool_label = st.text_input("Tool label (e.g. Invoice Generator)", value="")
        description = st.text_area("Short description (what the tool should do)", value="", height=90)
        submitted = st.form_submit_button("Generate / Update tool")

    if not submitted:
        return

    # Basic validation
    slug = tool_key.strip().lower().replace("-", "_")
    slug = "".join(ch for ch in slug if ch.isalnum() or ch == "_").strip("_")
    if not slug:
        st.error("Please provide a valid tool key.")
        return
    if not tool_label.strip():
        st.error("Please provide a tool label.")
        return

    module_path = f"tools.{slug}"
    repo_path   = f"streamlit_app/tools/{slug}.py"

    code = make_tool_scaffold(slug, tool_label.strip(), description.strip())
    commit_msg = f"feat(builder): add/update tool '{slug}' module"

    with st.spinner("Creating/updating tool file in GitHub…"):
        ok, msg = _create_or_update_file(repo_path, code, commit_msg)
    if ok:
        st.success(f"✅ {repo_path} {msg}.")
        st.code(code, language="python")
    else:
        st.error(f"❌ Could not write {repo_path}: {msg}")
        return

    with st.spinner("Registering tool in tools.yaml…"):
        ok2, msg2 = upsert_tool_in_tools_yaml(slug, tool_label.strip(), module_path)
    if ok2:
        st.success(f"✅ {msg2}")
        st.info("Tip: Use the sidebar to select the new tool. If you don't see it, click 'Rerun' in the app menu.")
    else:
        st.warning(f"⚠️ tools.yaml update issue: {msg2}")

