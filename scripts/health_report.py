import os
import sys
import yaml

def check_file_exists(path):
    return os.path.exists(path)

def check_yaml(path):
    try:
        with open(path, "r") as f:
            yaml.safe_load(f)
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    problems = []

    # 1. Check required files
    required_files = ["tools.yaml", "projects.yaml", "requirements.txt"]
    for f in required_files:
        if not check_file_exists(f):
            problems.append(f"Missing required file: {f}")

    # 2. Validate YAML files
    yaml_files = ["tools.yaml", "projects.yaml", "standards/departments.yaml", "standards/watchlist.yaml"]
    for f in yaml_files:
        if os.path.exists(f):
            ok, err = check_yaml(f)
            if not ok:
                problems.append(f"YAML error in {f}: {err}")

    # 3. Print summary
    if problems:
        print("❌ Repo Health Check Failed:")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    else:
        print("✅ Repo Health Check Passed")
        sys.exit(0)

if __name__ == "__main__":
    main()
