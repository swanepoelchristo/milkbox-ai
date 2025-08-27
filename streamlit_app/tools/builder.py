import os
import json
import base64
import time
from datetime import datetime
import requests
import streamlit as st
import yaml

# ------------- Config / Secrets -------------
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")             # e.g. "swanepoelchristo/milkbox-ai"
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")     # default branch name

API_ROOT = "https://api.github.com"
HDRS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# ------------- Small helpers -------------

def b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("utf-8")

def slugify(s: str) -> str:
    s = s.strip().lower().replace(" ", "_").replace("-", "_")
    return "".join(ch for ch in s if (ch.isalnum() or ch == "_")).strip("_")

def gh_get(path: str, params=None):
    url = f"{API_ROOT}{path}"
    r = requests.get(url, headers=HDRS, params=params or {})
    return r

def gh_post(path: str, payload: dict):
    url = f"{API_ROOT}{path}"
    r = requests.post(url, headers=HDRS, json=payload)
    return r

def gh_put(path: str, payload: dict):
    url = f"{API_ROOT}{path}"
    r = requests.put(url, headers=HDRS, json=payload)
    return r

def gh_content_get(path: str, ref: str = None):
    params = {"ref": ref} if ref else None
    r = gh_get(f"/repos/{GITHUB_REPO}/contents/{path}", params=params)
    return r

def gh_content_put(path: str, message: str, content_b64: str, branch: str, sha: str = None):
    payload = {"message": message, "content": content_b64, "branch": branch}
    if sha:
        payload["sha"] = sha
    return gh_put(f"/repos/{GITHUB_REPO}/contents/{path}", payload)

def create_branch(branch_name: str, from_branch: str = GITHUB_BRANCH):
    base = gh_get(f"/repos/{GITHUB_REPO}/git/ref/heads/{from_branch}")
    if base.status_code != 200:
        return False, f"Could not read base branch {from_branch}", None
    sha = base.json()["object"]["sha"]

    # Try create new ref
    r = gh_post(f"/repos/{GITHUB_REPO}/git/refs", {
        "ref": f"refs/heads/{branch_name}",
        "sha": sha
    })
    if r.status_code == 201:
        return True, "created", sha
    elif r.status_code == 422 and "Reference already exists" in r.text:
        return True, "exists", sha
    else:
        return False, f"Branch create failed: {r.status_code} {r.text}", None

def open_issue(title: str, body: str):
    r = gh_post(f"/repos/{GITHUB_REPO}/issues", {"title": title, "body": body})
    return r

def open_pr(title: str, head_branch: str, base_branch: str = GITHUB_BRANCH, body: str = ""):
    r = gh_post(f"/repos/{GITHUB_REPO}/pulls", {
        "title": title,
        "head": head_branch,
        "base": base_branch,
        "body": body
    })
    return r

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
    # do not duplicate
    if not any(t.get("key") == key for t in tools):
        tools.append({"key": key, "label": label, "module": f"tools.{key}"})
    ydata["tools"] = tools
    return ydata

def generate_tool_py(key: str, label: str, description: str) -> str:
    return f'''import streamlit as st

def render():
    st.header("🧩 {label}")
    st.write("{description}".strip())

    with st.form("{key}_form", clear_on_submit=False):
        example = st.text_input("Example input", value="")
        submitted = st.form_submit_button("Run")

    if submitted:
        st.success(f"✅ {label} ran! You typed: {{example}}")
'''

def format_issue_body(spec_path: str, brief: dict):
    nice = json.dumps(brief, indent=2)
    return f"""### Tool Spec

Spec file: `{spec_path}`

```json
{nice}
