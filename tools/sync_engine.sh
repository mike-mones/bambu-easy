#!/usr/bin/env bash
# Re-vendor the engine files from Mike's 3D Printing workspace.
#
# bambu_easy/_engine/ is a frozen mirror of validated logic from the source
# repo. Run this script when the upstream files change.

set -euo pipefail

SOURCE_REPO="${BAMBU_EASY_SOURCE_REPO:-$HOME/Documents/3D Printing}"
DEST_DIR="$(cd "$(dirname "$0")/.." && pwd)/bambu_easy/_engine"

if [ ! -d "$SOURCE_REPO/Scripts" ]; then
  echo "Source repo not found at: $SOURCE_REPO" >&2
  echo "Set BAMBU_EASY_SOURCE_REPO to override." >&2
  exit 1
fi

SHA="$(cd "$SOURCE_REPO" && git rev-parse HEAD)"
echo "Source repo: $SOURCE_REPO"
echo "Source commit: $SHA"

for f in print_profiles.py bs_validation.py bake_3mf_settings.py; do
  echo "  → vendoring $f"
  {
    echo "# VENDORED FROM $SOURCE_REPO/Scripts/$f at commit $SHA. Do not edit here — sync via tools/sync_engine.sh."
    echo
    cat "$SOURCE_REPO/Scripts/$f"
  } > "$DEST_DIR/$f"
done

echo "Done. Review the diff with: git diff bambu_easy/_engine/"
