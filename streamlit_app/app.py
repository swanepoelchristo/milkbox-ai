from typing import Dict, Any

# --- Ensure "tools.*" imports resolve ---
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent  # .../streamlit_app
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))
# ----------------------------------------

# ─────────────────────────────────────────────────────────
# Config
# tools.yaml lives at the REPO ROOT (not inside streamlit_app/)
# ─────────────────────────────────────────────────────────
TOOLS_FILE = Path(__file__).resolve().parent.parent / "tools.yaml"


# ─────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────
def load_tools_config() -> Dict[str, Any]:
    """
    Read tools.yaml from the repo root and return the parsed dict.
    Expected structure:
      tools:
        - key: invoice_gen
          label: Invoice Generator
          module: tools.invoice_gen
          section: Free
          description: ...
    """
    try:
        with open(TOOLS_FILE, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except FileNotFoundError as e:
        st.error(
            f"Failed to read tools.yaml: {e}\n\n"
            "Make sure tools.yaml is at the repository root."
        )
        return {"tools": []}
    except Exception as e:
        st.error(f"Error parsing tools.yaml: {e}")
        return {"tools": []}
    return cfg


def normalize_tools(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a list of tool dicts with safe defaults."""
    items = raw.get("tools", []) or []
    cleaned = []
    for t in items:
        if not isinstance(t, dict):
            continue
        key = str(t.get("key", "")).strip()
        module = str(t.get("module", "")).strip()
        label = str(t.get("label", key)).strip() or key
        section = t.get("section")  # optional
        description = t.get("description", "")

        if key and module:
            cleaned.append(
                {
                    "key": key,
                    "label": label,
                    "module": module,
                    "section": section,
                    "description": description,
                }
            )
    return cleaned


def tool_by_key(tools: List[Dict[str, Any]], key: str) -> Optional[Dict[str, Any]]:
    for t in tools:
        if t["key"] == key:
            return t
    return None


# ─────────────────────────────────────────────────────────
# Sidebar UI
# ─────────────────────────────────────────────────────────
def render_sidebar(tools: List[Dict[str, Any]]) -> Optional[str]:
    """
    Render a grouped sidebar if 'section' is present in YAML.
    Falls back to a single list otherwise.
    Returns the selected tool key.
    """
    st.sidebar.title("Milkbox AI Toolbox")

    if not tools:
        st.sidebar.info("No tools found in tools.yaml.")
        return None

    # Decide grouping
    has_sections = any(t.get("section") for t in tools)
    selected_key = st.session_state.get("selected_tool")

    if has_sections:
        # Group by 'section' while keeping insertion order
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for t in tools:
            sec = t.get("section") or "Tools"
            groups.setdefault(sec, []).append(t)

        for sec_name, items in groups.items():
            st.sidebar.markdown(f"### {sec_name}")
            for t in items:
                if st.sidebar.button(f"Open: {t['label']}", key=f"btn_{t['key']}"):
                    selected_key = t["key"]
    else:
        # Simple radio list
        labels = [t["label"] for t in tools]
        keys = [t["key"] for t in tools]
        default_index = 0
        if selected_key in keys:
            default_index = keys.index(selected_key)
        idx = st.sidebar.radio("Choose a tool", options=list(range(len(keys))), format_func=lambda i: labels[i], index=default_index)
        selected_key = keys[idx]

    # Persist selection
    st.session_state["selected_tool"] = selected_key
    return selected_key


# ─────────────────────────────────────────────────────────
# Main area
# ─────────────────────────────────────────────────────────
def render_selected_tool(tools: List[Dict[str, Any]], key: Optional[str]) -> None:
    """
    Import and render the selected tool.

    NOTE: We import EXACTLY what the YAML specifies in 'module'
    (e.g., 'tools.invoice_gen'), without auto-prefixing. This keeps
    imports consistent and avoids ModuleNotFoundError for valid paths.
    """
    if not key:
        st.header("Milkbox AI Toolbox")
        st.write("Select a tool from the sidebar to begin.")
        return

    t = tool_by_key(tools, key)
    if not t:
        st.error(f"Tool '{key}' not found in tools.yaml")
        return

    module_path = t["module"]
    try:
        mod = importlib.import_module(module_path)
    except ModuleNotFoundError as e:
        st.error(
            f"Couldn't import module `{module_path}`.\n\n"
            "Make sure the module path in tools.yaml matches the file on disk.\n"
            f"Details: {e}"
        )
        return
    except Exception as e:
        st.error(f"Error importing `{module_path}`: {e}")
        return

    # Render
    if hasattr(mod, "render"):
        try:
            mod.render()
        except Exception as e:
            st.error(f"Error while rendering `{t['label']}`: {e}")
    else:
        st.error(f"Module `{module_path}` has no function `render()`.")


# ─────────────────────────────────────────────────────────
# App entrypoint
# ─────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="Milkbox AI Toolbox", layout="wide")

    cfg = load_tools_config()
    tools = normalize_tools(cfg)

    selected = render_sidebar(tools)
    render_selected_tool(tools, selected)


if __name__ == "__main__":
    main()
