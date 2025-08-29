#!/usr/bin/env python3
import sys, json
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parents[1]
DEPTS = REPO / "standards" / "departments.yaml"
OUT   = REPO / "standards" / "sop_state.json"

def load_yaml(p):
    if not p.exists(): return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}

def list_files(base: Path):
    if not base.exists(): return []
    return [p for p in base.rglob("*") if p.is_file()]

def main():
    cfg = load_yaml(DEPTS)
    depts = cfg.get("departments", [])
    summary = {"departments": []}
    any_missing = False

    for d in depts:
        key = d.get("key","?")
        name = d.get("name","Department")
        sop_dir_rel = d.get("sop_dir","")
        expected = d.get("expected_sops", [])
        sop_dir = (REPO / sop_dir_rel).resolve() if sop_dir_rel else None

        found = set()
        if sop_dir:
            for f in list_files(sop_dir):
                found.add(f.stem.lower())

        present, missing = [], []
        for sop in expected:
            token = sop.split()[0].lower()  # e.g. "SOP-001"
            ok = any(token in s for s in found)
            (present if ok else missing).append(sop)

        if missing: any_missing = True

        summary["departments"].append({
            "key": key, "name": name,
            "sop_dir": sop_dir_rel,
            "present": present, "missing": missing
        })

    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if any_missing:
        print("❌ Missing SOPs detected\n")
        print(json.dumps(summary, indent=2))
        sys.exit(1)
    else:
        print("✅ All required SOPs present")
        sys.exit(0)

if __name__ == "__main__":
    main()
