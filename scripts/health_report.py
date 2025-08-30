#!/usr/bin/env python3
"""
Repo Health reporter.

Checks (lightweight):
- Required workflows exist
- Required scripts exist
- smoke.yml points to scripts/test_imports.py (not .github/scripts/..)
- README and LICENSE presence (warn only)
- Last commit timestamp (info)

Exit codes:
 0 = OK or only warnings
 1 = Critical failures (missing required files / bad paths) or internal error
"""

from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # avoid hard dep; we parse minimally if missing

CHECKS = []

def add(check: str, result: str, details: str, severity: str = "info"):
    CHECKS.append({"check": check, "result": result, "details": details, "severity": severity})

def file_exists(path: str) -> bool:
    return Path(path).exists()

def read_yaml(path: str):
    text = Path(path).read_text(encoding="utf-8")
    if yaml:
        return yaml.safe_load(text)
    # Micro parser fallback: we only need to search for the script path string
    return {"__raw__": text}

def git_last_commit_iso() -> str:
    try:
        out = subprocess.check_output(["git", "log", "-1", "--format=%cI"], text=True).strip()
        return out or "unknown"
    except Exception:
        return "unknown"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="Write Markdown report to file", default="")
    ap.add_argument("--strict", action="store_true", help="Treat warnings as failures (exit 1)")
    args = ap.parse_args()

    critical_failures = 0
    warnings = 0

    # Required files
    reqs = [
        (".github/workflows/smoke.yml", "Required smoke workflow is missing"),
        (".github/workflows/repo_health.yml", "Required repo health workflow is missing"),
        ("scripts/test_imports.py", "Import smoke script missing"),
        ("scripts/health_report.py", "Health report script missing (this one)"),
    ]
    for path, msg in reqs:
        if file_exists(path):
            add(f"Presence: {path}", "OK", "Found")
        else:
            add(f"Presence: {path}", "FAIL", msg, severity="fail")
            critical_failures += 1

    # Validate smoke path points to scripts/test_imports.py
    smk = Path(".github/workflows/smoke.yml")
    if smk.exists():
        try:
            data = read_yaml(str(smk))
            raw = ""
            if isinstance(data, dict):
                raw = ""
            else:
                raw = ""
            # Generic text search works whether parsed or raw
            text = smk.read_text(encoding="utf-8")
            if "scripts/test_imports.py" in text and ".github/scripts/test_imports.py" not in text:
                add("smoke.yml import path", "OK", "Uses scripts/test_imports.py")
            else:
                add("smoke.yml import path", "FAIL", "Path should be scripts/test_imports.py", severity="fail")
                critical_failures += 1
        except Exception as e:
            add("smoke.yml parse", "FAIL", f"Error reading: {e}", severity="fail")
            critical_failures += 1

    # README / LICENSE (warn only)
    if file_exists("README.md"):
        add("README.md", "OK", "Found")
    else:
        add("README.md", "WARN", "Missing README.md", severity="warn")
        warnings += 1

    if file_exists("LICENSE") or file_exists("LICENSE.md"):
        add("LICENSE", "OK", "Found")
    else:
        add("LICENSE", "WARN", "Missing LICENSE", severity="warn")
        warnings += 1

    # Last commit info (informational)
    add("Last commit (git)", "INFO", git_last_commit_iso(), severity="info")

    # Build Markdown
    lines = [
        "# Repo Health",
        "",
        "| Check | Result | Details |",
        "|---|---|---|",
    ]
    for c in CHECKS:
        lines.append(f"| {c['check']} | {c['result']} | {c['details']} |")
    lines.append("")
    if critical_failures:
        lines.append(f"**Status:** ❌ {critical_failures} critical failure(s).")
    elif warnings and args.strict:
        lines.append(f"**Status:** ❌ {warnings} warning(s) (strict mode).")
    elif warnings:
        lines.append(f"**Status:** ⚠️ {warnings} warning(s).")
    else:
        lines.append("**Status:** ✅ All checks passed.")

    md = "\n".join(lines)

    # Write out
    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
    if "GITHUB_STEP_SUMMARY" in os.environ:
        try:
            Path(os.environ["GITHUB_STEP_SUMMARY"]).write_text(md, encoding="utf-8")
        except Exception:
            pass

    # Exit policy: only non-zero on real failures (or strict warnings)
    if critical_failures:
        return 1
    if args.strict and warnings:
        return 1
    return 0

if __name__ == "__main__":
    import os
    sys.exit(main())
