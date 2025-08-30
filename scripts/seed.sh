#!/usr/bin/env bash
set -euo pipefail
OWNER=$1
NAME=$2

TMP=$(mktemp -d)
cd "$TMP"
gh repo clone "$OWNER/$NAME" repo -- --depth=1
cd repo

mkdir -p .github/workflows
mkdir -p .github

# CodeQL
cat > .github/workflows/codeql.yml <<'YML'
name: "CodeQL"
on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]
  schedule:
    - cron: "0 3 * * 1"
permissions:
  contents: read
  security-events: write
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: python
      - uses: github/codeql-action/analyze@v3
YML

# CI Smoke
cat > .github/workflows/ci-smoke.yml <<'YML'
name: "CI Smoke"
on:
  workflow_dispatch:
  push:
    branches: [ "main" ]
jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Smoke test for $(basename $GITHUB_REPOSITORY) ✔"
YML

# Dependabot
cat > .github/dependabot.yml <<'YML'
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
YML

git config user.email "actions@users.noreply.github.com"
git config user.name  "github-actions[bot]"
git add .github
if ! git diff --cached --quiet; then
  git commit -m "chore: bootstrap CI (CodeQL, Smoke) + Dependabot"
  git push origin HEAD
fi

# Labels
add_label () {
  gh api -X POST /repos/$OWNER/$NAME/labels \
    -f name="$1" -f color="$2" -f description="$3" >/dev/null 2>&1 || true
}
add_label "bug" "d73a4a" "Something isn't working"
add_label "docs" "0075ca" "Documentation changes"
add_label "enhancement" "a2eeef" "New feature"
add_label "security" "b60205" "Security related"

# Branch protection (main)
gh api -X PUT "/repos/$OWNER/$NAME/branches/main/protection" \
  -f required_status_checks='null' \
  -f enforce_admins=true \
  -f required_pull_request_reviews.required_approving_review_count=1 \
  -f restrictions='null' >/dev/null

# Trigger smoke
gh workflow run "CI Smoke" -R "$OWNER/$NAME" || true
