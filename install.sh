#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAMP="$(date +%Y%m%d%H%M%S)"
HOST="hermes"
TARGET=""
MODE="auto"
RUN_CHECKS=1

usage() {
  cat <<'EOF'
Usage: ./install.sh [--host hermes|openclaw|generic] [--target PATH] [--overwrite-existing|--preserve-existing] [--no-check] [PATH]

Clean installs automatically inject the Digital Office entrypoint and make the
suite rules authoritative for the target host. If an existing host has local
rules or personal runtime data, choose one:

  --overwrite-existing   Back up local rule files, then replace them with the Digital Office entrypoint.
  --preserve-existing    Keep local rule files active and install Digital Office as a side-by-side bundle.

Default targets:
  hermes    ~/.hermes
  openclaw  ~/.openclaw
  generic   ~/.digital-office-agent
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --host)
      HOST="${2:-}"
      shift 2
      ;;
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --overwrite-existing)
      MODE="overwrite"
      shift
      ;;
    --preserve-existing)
      MODE="preserve"
      shift
      ;;
    --no-check)
      RUN_CHECKS=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --*)
      echo "install.sh: unknown option $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [ -n "$TARGET" ]; then
        echo "install.sh: target specified more than once" >&2
        usage >&2
        exit 2
      fi
      TARGET="$1"
      shift
      ;;
  esac
done

case "$HOST" in
  hermes)
    TARGET="${TARGET:-$HOME/.hermes}"
    ENTRYPOINTS=("SOUL.md")
    ;;
  openclaw)
    TARGET="${TARGET:-${OPENCLAW_HOME:-$HOME/.openclaw}}"
    ENTRYPOINTS=("AGENTS.md")
    ;;
  generic)
    TARGET="${TARGET:-$HOME/.digital-office-agent}"
    ENTRYPOINTS=("AGENTS.md")
    ;;
  *)
    echo "install.sh: unsupported host '$HOST' (expected hermes, openclaw, or generic)" >&2
    exit 2
    ;;
esac

MANAGED_MARKER="digital-office-managed-entrypoint"

path_has_user_data() {
  local path="$1"
  if [ ! -d "$path" ]; then
    return 1
  fi
  find "$path" -mindepth 1 \( -name ".gitignore" -o -name "_template" \) -prune -o -print -quit | grep -q .
}

dirty_reasons=()
if [ -d "$TARGET" ]; then
  for entrypoint in "${ENTRYPOINTS[@]}" SOUL.md AGENTS.md; do
    if [ -f "$TARGET/$entrypoint" ] && ! grep -q "$MANAGED_MARKER" "$TARGET/$entrypoint"; then
      dirty_reasons+=("existing unmanaged rule file: $entrypoint")
    fi
  done
  if [ -f "$TARGET/agent-system/settings/user-preferences.md" ]; then
    dirty_reasons+=("existing user preferences")
  fi
  for data_path in \
    "$TARGET/agent-system/projects" \
    "$TARGET/agent-system/knowledge/company" \
    "$TARGET/agent-system/knowledge/spaces" \
    "$TARGET/agent-system/rules/projects" \
    "$TARGET/agent-system/tasks" \
    "$TARGET/agent-system/runs"; do
    if path_has_user_data "$data_path"; then
      dirty_reasons+=("existing runtime data: ${data_path#$TARGET/}")
    fi
  done
fi

if [ "$MODE" = "auto" ] && [ "${#dirty_reasons[@]}" -gt 0 ]; then
  {
    echo "Digital Office found an existing non-clean $HOST runtime at $TARGET."
    echo "Choose --preserve-existing to keep both rule sets, or --overwrite-existing to back up and replace local host rules."
    echo "Detected:"
    for reason in "${dirty_reasons[@]}"; do
      echo "  - $reason"
    done
  } >&2
  exit 2
fi

if [ "$MODE" = "auto" ]; then
  MODE="overwrite"
fi

if [ "$MODE" = "preserve" ]; then
  INSTALL_ROOT="$TARGET/digital-office"
else
  INSTALL_ROOT="$TARGET"
fi

mkdir -p "$INSTALL_ROOT/scripts" "$INSTALL_ROOT/profiles" "$INSTALL_ROOT/skills"

sync_dir() {
  local src="$1" dst="$2"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a "$src" "$dst"
  else
    cp -R "$src" "$dst"
  fi
}

sync_with_excludes() {
  local src="$1" dst="$2"
  shift 2
  mkdir -p "$dst"
  if command -v rsync >/dev/null 2>&1; then
    local args=(-a)
    local pattern
    for pattern in "$@"; do
      args+=(--exclude "$pattern")
    done
    rsync "${args[@]}" "$src/" "$dst/"
  else
    local tar_args=()
    local pattern
    for pattern in "$@"; do
      tar_args+=(--exclude "./${pattern#/}")
    done
    tar -C "$src" "${tar_args[@]}" -cf - . | tar -C "$dst" -xf -
  fi
}

AGENT_RUNTIME_EXCLUDES=(
  "/logs/*"
  "/tmp/*"
  "/runs/*"
  "/tasks/*"
  "/approvals/*"
  "/judgments/*"
  "/notifications/*"
  "/settings/*"
  "/rule-proposals/*"
  "/iterations/proposals/*"
  "/iterations/status/*"
  "/iterations/applied/*"
  "/harness/reports/*"
  "/evals/reports/*"
  "/data-sharing/consent.json"
  "/data-sharing/exports/*"
  "/data-sharing/outbox/*"
  "/data-sharing/receipts/*"
  "/agent-requests/outbox/*"
  "/agent-requests/status/*"
  "/agent-requests/receipts/*"
  "/agent-improvements/*/drafts/*"
  "/agent-improvements/*/approved/*"
  "/agent-plugins/packages/*"
  "/agent-plugins/reports/*"
  "/agent-plugins/status/*"
  "/knowledge/company/entries/*"
  "/knowledge/company/index/*"
  "/knowledge/spaces/*"
  "/knowledge/mounts/*"
  "/projects/*"
  "/models/cache/*"
  "/bin/__pycache__/*"
)

PROFILE_RUNTIME_EXCLUDES=(
  "*/.skills_prompt_snapshot.json"
  "*/.env"
  "*/auth.json"
  "*/auth.lock"
  "*/models_dev_cache.json"
  "*/state.db*"
  "*/memory_store.db*"
  "*/keymemory.db*"
  "*/sessions/*"
  "*/logs/*"
  "*/__pycache__/*"
)

sync_with_excludes "$SOURCE_DIR/agent-system" "$INSTALL_ROOT/agent-system" "${AGENT_RUNTIME_EXCLUDES[@]}"
if [ -d "$SOURCE_DIR/agent-system/projects/_template" ]; then
  sync_dir "$SOURCE_DIR/agent-system/projects/_template/" "$INSTALL_ROOT/agent-system/projects/_template/"
fi
sync_dir "$SOURCE_DIR/scripts/" "$INSTALL_ROOT/scripts/"
sync_with_excludes "$SOURCE_DIR/profiles" "$INSTALL_ROOT/profiles" "${PROFILE_RUNTIME_EXCLUDES[@]}"
sync_dir "$SOURCE_DIR/skills/" "$INSTALL_ROOT/skills/"
cp "$SOURCE_DIR/README.md" "$INSTALL_ROOT/README.md"
cp "$SOURCE_DIR/README.zh-CN.md" "$INSTALL_ROOT/README.zh-CN.md"
cp "$SOURCE_DIR/CHANGELOG.md" "$INSTALL_ROOT/CHANGELOG.md"
cp "$SOURCE_DIR/install.sh" "$INSTALL_ROOT/install.sh"
cp "$SOURCE_DIR/update" "$INSTALL_ROOT/update"
cp "$SOURCE_DIR/digital-office-gui" "$INSTALL_ROOT/digital-office-gui"

mkdir -p \
  "$INSTALL_ROOT/agent-system/logs" \
  "$INSTALL_ROOT/agent-system/tmp" \
  "$INSTALL_ROOT/agent-system/runs" \
  "$INSTALL_ROOT/agent-system/tasks" \
  "$INSTALL_ROOT/agent-system/approvals" \
  "$INSTALL_ROOT/agent-system/judgments" \
  "$INSTALL_ROOT/agent-system/notifications" \
  "$INSTALL_ROOT/agent-system/settings" \
  "$INSTALL_ROOT/agent-system/rule-proposals" \
  "$INSTALL_ROOT/agent-system/harness/reports" \
  "$INSTALL_ROOT/agent-system/evals/reports" \
  "$INSTALL_ROOT/agent-system/knowledge/company/entries" \
  "$INSTALL_ROOT/agent-system/knowledge/company/index" \
  "$INSTALL_ROOT/agent-system/knowledge/spaces" \
  "$INSTALL_ROOT/agent-system/knowledge/mounts"

if [ "$MODE" = "preserve" ]; then
  for entrypoint in "${ENTRYPOINTS[@]}"; do
    cp "$SOURCE_DIR/SOUL.md" "$INSTALL_ROOT/$entrypoint"
  done
  cp "$SOURCE_DIR/SOUL.md" "$INSTALL_ROOT/SOUL.md"
else
  for entrypoint in "${ENTRYPOINTS[@]}"; do
    if [ -f "$TARGET/$entrypoint" ]; then
      cp "$TARGET/$entrypoint" "$TARGET/$entrypoint.before-digital-office.$STAMP"
    fi
    cp "$SOURCE_DIR/SOUL.md" "$TARGET/$entrypoint"
  done

  if [ "$HOST" = "openclaw" ] || [ "$HOST" = "generic" ]; then
    cp "$SOURCE_DIR/SOUL.md" "$TARGET/SOUL.md"
  fi
fi

chmod +x "$INSTALL_ROOT/scripts/agent-router"
chmod +x "$INSTALL_ROOT/agent-system/bin/office-system"
chmod +x "$INSTALL_ROOT/agent-system/bin/digital-office-gui"
chmod +x "$INSTALL_ROOT/agent-system/bin/harness-check"
chmod +x "$INSTALL_ROOT/agent-system/bin/harness-runner"
chmod +x "$INSTALL_ROOT/agent-system/bin/install-skill-sources"
chmod +x "$INSTALL_ROOT/agent-system/bin/install-local-models"
chmod +x "$INSTALL_ROOT/agent-system/bin/update-system"
chmod +x "$INSTALL_ROOT/agent-system/bin/product-update"
chmod +x "$INSTALL_ROOT/install.sh"
chmod +x "$INSTALL_ROOT/update"
chmod +x "$INSTALL_ROOT/digital-office-gui"

if [ "$RUN_CHECKS" -eq 1 ]; then
  "$INSTALL_ROOT/agent-system/bin/install-skill-sources"
  "$INSTALL_ROOT/scripts/agent-router" --health
  "$INSTALL_ROOT/agent-system/bin/office-system" health
  "$INSTALL_ROOT/agent-system/bin/harness-check"
  "$INSTALL_ROOT/agent-system/bin/harness-runner" --task all --no-write
  "$INSTALL_ROOT/agent-system/bin/product-update" status
fi

if [ "$MODE" = "preserve" ]; then
  echo "Digital Office Agent System installed side-by-side to $INSTALL_ROOT for $HOST"
  echo "Existing $HOST entrypoint files under $TARGET were preserved."
else
  echo "Digital Office Agent System installed to $TARGET for $HOST"
fi
