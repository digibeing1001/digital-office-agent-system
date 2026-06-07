#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-$HOME/.hermes}"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAMP="$(date +%Y%m%d%H%M%S)"

mkdir -p "$TARGET/scripts" "$TARGET/profiles" "$TARGET/skills"

if [ -f "$TARGET/SOUL.md" ]; then
  cp "$TARGET/SOUL.md" "$TARGET/SOUL.before-digital-office.$STAMP.md"
fi

rsync -a "$SOURCE_DIR/agent-system/" "$TARGET/agent-system/"
rsync -a "$SOURCE_DIR/scripts/" "$TARGET/scripts/"
rsync -a "$SOURCE_DIR/profiles/" "$TARGET/profiles/"
rsync -a "$SOURCE_DIR/skills/" "$TARGET/skills/"
cp "$SOURCE_DIR/SOUL.md" "$TARGET/SOUL.md"

chmod +x "$TARGET/scripts/agent-router"
chmod +x "$TARGET/agent-system/bin/office-system"
chmod +x "$TARGET/agent-system/bin/harness-check"
chmod +x "$TARGET/agent-system/bin/harness-runner"
chmod +x "$TARGET/agent-system/bin/install-local-models"
chmod +x "$TARGET/agent-system/bin/update-system"
chmod +x "$TARGET/agent-system/bin/product-update"

"$TARGET/scripts/agent-router" --health
"$TARGET/agent-system/bin/office-system" health
"$TARGET/agent-system/bin/harness-check"
"$TARGET/agent-system/bin/harness-runner" --task all --no-write
"$TARGET/agent-system/bin/product-update" status

echo "Digital Office Agent System installed to $TARGET"
