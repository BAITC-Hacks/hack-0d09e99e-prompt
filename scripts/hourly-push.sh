#!/usr/bin/env bash
# Push local changes every hour. Skip if the tree is clean.
set -euo pipefail
cd "$(dirname "$0")/.."

while true; do
  sleep 3600
  git add -A
  if git diff --cached --quiet; then
    echo "$(date '+%Y-%m-%d %H:%M') nothing to push"
    continue
  fi
  git commit -m "$(cat <<EOF
feat: hourly sync $(date '+%Y-%m-%d %H:%M')

EOF
)"
  git push origin HEAD
done
