#!/usr/bin/env python3
import argparse
import importlib
import json
import os
import sys
import traceback
from pathlib import Path

try:
    import yaml
except Exception as e:  # pyyaml should be installed by workflow
    print("ERROR: PyYAML not installed. Install pyyaml.")
    sys.exit(2)


def parse_args():
    ap = argparse.ArgumentParser(description="Repo Health Report")
    ap.add_argument("--tools-yaml", default="tools.yaml")
    ap.add_argument("--tools-dir", default="streamlit_app/tools")
    ap.add_argument("--package-root", default="streamlit_app")
    ap.add_argument("--out-md", default="repo-health-report.md")
    ap.add_argument("--out-json", default="repo-health-report.json")
    return ap.parse_args()


def read_tools_yaml(p: Path):
    if not p.exists():
        return {"error": f"tools.yaml not found at {p}"}, []
    try:
        data = yaml.safe_load(p.read_text())
    except Exception as e:
        return {"error": f"Failed to parse tools.yaml: {e}"}, []
    items = []
    for item in (data.get("tools") or []):
        key = item.get("key")
        label = item.get("label")
        module = item.get("module")
        items.append({"key": key, "label": label, "module": module})
    return {}, items


def ensure_package_marker(package_root: Path, tools_dir: Path):
    issues = []
    # The package root must have __init__.py
    if not (package_root / "__init__.py").exists():
        issues.append(f"Missing package marker: {package_root}/__init__.py")

    # tools dir must have __init__.py
    if not (tools_dir / "__init__.py").exists():
        issues.append(f"Missing package marker: {tools_dir}/__init__.py")
    return issues


def module_to_path(module: str, package_root: Path):
    """
    Convert a module like 'tools.hello' into a file path under package_root.
    e.g. streamlit_app/tools/hello.py or streamlit_app/tools/hello/__init__.py
    """
    if not module or "." not in module:
        return None
    parts = module.split(".")
    if parts[0] != "tools":
        # We only validate 'tools.*' here
        return None
    rel = Path(*parts)  # tools/hello
    # Try file
    py = package_root / f"{rel}.py"
    if py.exists():
        return py
    # Try package dir
    pkg = package_root / rel / "__init__.py"
    if pkg.exists():
        return pkg
    return None


def try_import(module: str, package_root: Path):
    """
    Attempt to import a module by name (e.g. tools.hello)
    Adjust sys.path so that 'streamlit_app' is importable as a package root.
    """
    try:
        # Insert the parent of package_root on sys.path
        root_parent = str(package_root.parent.resolve())
        if root_parent not in sys.path:
            sys.path.insert(0, root_parent)
        importlib.invalidate_caches()
        importlib.import_module(module)
        return True, ""
    except Exception as e:
        return False, "".join(traceback.format_exception_only(type(e), e)).strip()


def main():
    args = parse_args()
    repo = Path.cwd()
    tools_yaml_path = (repo / args.tools_yaml).resolve()
    tools_dir = (repo / args.tools_dir).resolve()
    package_root = (repo / args.package_root).resolve()

    report = {
        "repo": str(repo),
        "python": sys.version,
        "env": {k: v for k, v in os.environ.items() if k.startswith("GITHUB_")},
        "checks": [],
        "failed_checks": 0,
    }

    # 1) tools.yaml
    hdr, tools_list = read_tools_yaml(tools_yaml_path)
    if hdr:
        report["checks"].append({"name": "tools.yaml parse", "ok": False, "details": hdr["error"]})
        report["failed_checks"] += 1
    else:
        report["checks"].append({"name": "tools.yaml parse", "ok": True, "details": f"{len(tools_list)} tool entries"})

    # 2) package markers
    pkg_issues = ensure_package_marker(package_root, tools_dir)
    if pkg_issues:
        report["checks"].append({"name": "package markers", "ok": False, "details": "; ".join(pkg_issues)})
        report["failed_checks"] += 1
    else:
        report["checks"].append({"name": "package markers", "ok": True, "details": "OK"})

    # 3) Validate each tools.yaml entry: path exists + import works
    for t in tools_list:
        module = t.get("module")
        key = t.get("key")
        label = t.get("label")
        entry_name = f"tool[{key}] {label} -> {module}"

        if not module:
            report["checks"].append({"name": entry_name, "ok": False, "details": "Missing 'module' field"})
            report["failed_checks"] += 1
            continue

        path = module_to_path(module, package_root)
        if not path:
            report["checks"].append({"name": entry_name, "ok": False, "details": f"No file/package found for {module}"})
            report["failed_checks"] += 1
            continue

        ok, err = try_import(module, package_root)
        if ok:
            report["checks"].append({"name": entry_name, "ok": True, "details": f"Import OK ({path.relative_to(repo)})"})
        else:
            report["checks"].append({"name": entry_name, "ok": False, "details": f"Import error: {err}"})
            report["failed_checks"] += 1

    # 4) Write JSON
    Path(args.out_json).write_text(json.dumps(report, indent=2))

    # 5) Write Markdown
    lines = []
    lines.append(f"# Repo Health Report\n")
    lines.append(f"- Repo: `{report['repo']}`")
    lines.append(f"- Python: `{report['python']}`")
    lines.append(f"- Failed checks: **{report['failed_checks']}**\n")
    lines.append("## Checks")
    for c in report["checks"]:
        badge = "✅" if c["ok"] else "❌"
        lines.append(f"- {badge} **{c['name']}** — {c['details']}")
    Path(args.out_md).write_text("\n".join(lines))

    # Exit non-zero if any failures (workflow also enforces this)
    if report["failed_checks"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
