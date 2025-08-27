import os
import json
import base64
from datetime import datetime
from typing import Optional, Tuple

import requests
import streamlit as st
import yaml

# ─────────────────────────────────────────────────────────
# Secrets / Config  (set in Streamlit Cloud → App → Settings → Secrets)
#   GITHUB_TOKEN:  a PAT with 'repo' scope
#   GITHUB_REPO:   "owner/repo"   e.g. "swanepoelchristo/milkbox-ai"
#   GITHUB_BRANCH: default branch (optional, defaults to "main")
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
# Small helpers
# ─────────────────────────────────────────────────────────
def b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("utf-8")


def slugify(s: str) -> str:
    s = (s or "").strip().lower().replace(" ", "_").replace("-", "_")
    return "".join(ch for ch in s if (ch.isalnum() or ch == "_")).strip("_")


def py_str(s: str) -> str:
    """
    Return a safe Python string literal for s.
    Uses json.dumps so quotes/newlines are escaped correctly.
    """
    return json.dumps("" if s is None else str(s))


def gh_get(path: str, params=None):
    return requests.get(f"{API_ROOT}{path}", headers=HDRS, params=params or {})


def gh_post(path: str, payload: dict):
    return requests.post(f"{API_ROOT}{path}", headers=HDRS, json=payload)


def gh_put(path: str, payload: dict):
    return requests.put(f"{API_ROOT}{path}", headers=HDRS, json=payload)


def gh_content_get(path: str, ref: Optional[str] = None):
    params = {"ref": ref} if ref else None
    return gh_get(f"/repos/{GITHUB_REPO}/contents/{path}", params=params)


def gh_content_put(path: str, message: str, content_b64: str, branch: str, sha: Optional[str] = None):
    payload = {"message": message, "content": content_b64, "branch": branch}
    if sha:
        payload["sha"] = sha
    return gh_put(f"/repos/{GITHUB_REPO}/contents/{path}", payload)


# ─────────────────────────────────────────────────────────
# Branch / PR / Issues
# ─────────────────────────────────────────────────────────
def create_branch(branch_name: str, from_branch: str = GITHUB_BRANCH) -> Tuple[bool, str, Optional[str]]:
    base = gh_get(f"/repos/{GITHUB_REPO}/git/ref/heads/{from_branch}")
    if base.status_code != 200:
        return False, f"Could not read base branch {from_branch}", None
    sha = base.json()["object"]["sha"]

    r = gh_post(f"/repos/{GITHUB_REPO}/git/refs", {"ref": f"refs/heads/{branch_name}", "sha": sha})
    if r.status_code == 201:
        return True, "created", sha
    if r.status_code == 422 and "Reference already exists" in r.text:
        return True, "exists", sha
    return False, f"Branch create failed: {r.status_code} {r.text}", None


def open_issue(title: str, body: str):
    return gh_post(f"/repos/{GITHUB_REPO}/issues", {"title": title, "body": body})


def open_pr(title: str, head_branch: str, base_branch: str = GITHUB_BRANCH, body: str = ""):
    return gh_post(
        f"/repos/{GITHUB_REPO}/pulls",
        {"title": title, "head": head_branch, "base": base_branch, "body": body},
    )


# ─────────────────────────────────────────────────────────
# YAML read/update
# ─────────────────────────────────────────────────────────
def fetch_yaml_from_main(path="tools.yaml"):
    r = gh_content_get(path, ref=GITHUB_BRANCH)
    if r.status_code != 200:
        return None, None, f"Could not read {path}: {r.status_code}"
    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    sha = data["sha"]
    try:
        y = yaml.safe_load(content) or {}
    except Exception as e:
        return None, None, f"YAML parse error: {e}"
    return y, sha, None


def ensure_tools_entry(ydata: dict, key: str, label: str):
    ydata = ydata or {}
    tools = ydata.get("tools", [])
    if not any(isinstance(t, dict) and t.get("key") == key for t in tools):
        tools.append({"key": key, "label": label, "module": f"tools.{key}"})
    ydata["tools"] = tools
    return ydata


# ─────────────────────────────────────────────────────────
# Code generation (safe)
# ─────────────────────────────────────────────────────────
def generate_tool_py(key: str, label: str, description: str) -> str:
    """
    Build a minimal Streamlit tool with safely escaped strings.
    """
    label_lit = py_str(label or "New Tool")
    desc_lit = py_str(description or "New tool created by the Tool Builder.")
    form_key_lit = py_str(f"{key}_form")

    return f'''import streamlit as st

def render():
    st.header("🧩 " + {label_lit})
    st.write({desc_lit})

    with st.form({form_key_lit}, clear_on_submit=False):
        example = st.text_input("Example input", value="")
        submitted = st.form_submit_button("Run")

    if submitted:
        st.success("✅ " + {label_lit} + " ran! You typed: " + str(example))
'''


def format_issue_body(spec_path: str, brief: dict) -> str:
    nice = json.dumps(brief, indent=2)
    return f"""### Tool Spec

Spec file: `{spec_path}`

```json
{nice}

