#!/usr/bin/env bash
# Restores the reference repos listed in REPOS.json as siblings of arcon/,
# at the same relative location, on a fresh clone of this perceptron repo.
#
# Usage:
#   ./scripts/clone-reference-repos.sh              # clone all, skip existing dirs
#   ./scripts/clone-reference-repos.sh --update      # also git pull existing clones
#
# Requires: git, python3 (for JSON parsing), no other dependencies.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT_DIR/REPOS.json"
UPDATE=false

if [[ "${1:-}" == "--update" ]]; then
  UPDATE=true
fi

if [[ ! -f "$MANIFEST" ]]; then
  echo "Manifest not found: $MANIFEST" >&2
  exit 1
fi

# Emit "dir|url|branch" lines from REPOS.json without requiring jq.
python3 -c "
import json, sys
with open('$MANIFEST') as f:
    data = json.load(f)
for r in data['repos']:
    print(f\"{r['dir']}|{r['url']}|{r['branch']}\")
" | while IFS='|' read -r dir url branch; do
  target="$ROOT_DIR/$dir"

  if [[ -d "$target/.git" ]]; then
    if [[ "$UPDATE" == true ]]; then
      echo "==> Updating $dir (branch $branch)"
      git -C "$target" fetch origin "$branch" --quiet
      git -C "$target" checkout "$branch" --quiet
      git -C "$target" merge --ff-only "origin/$branch" || \
        echo "    (skipped: local changes or diverged history in $dir)"
    else
      echo "==> Skipping $dir (already cloned; pass --update to pull)"
    fi
    continue
  fi

  echo "==> Cloning $dir from $url (branch $branch)"
  git clone --branch "$branch" --single-branch "$url" "$target"
done

echo
echo "Done. Reference repos are siblings of arcon/ under $ROOT_DIR."
echo "See REPOS.json for exact commits this workspace's analysis docs were written against;"
echo "repos will now be at their own latest HEAD, which may differ."
