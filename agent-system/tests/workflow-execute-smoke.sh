#!/usr/bin/env bash
set -euo pipefail

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

cp -a "$SOURCE_ROOT/agent-system" "$tmp/agent-system"
mkdir -p "$tmp/scripts"
cp -a "$SOURCE_ROOT/scripts/agent-router" "$tmp/scripts/agent-router"

export DIGITAL_OFFICE_SYSTEM_HOME="$tmp/agent-system"
export DIGITAL_OFFICE_CODEX_COMMAND="/bin/echo"

office="$tmp/agent-system/bin/office-system.py"
gateway="$tmp/agent-system/bin/model-gateway"

"$gateway" configure --agent writer --mode host --local-runtime codex --confirmed >/tmp/digital-office-workflow-exec-runtime.json
"$office" workflow-start \
  --tenant smoke \
  --deployment local \
  --user smoke \
  --role owner \
  --agent writer \
  --task "draft a tiny internal memo" \
  --execute \
  --runtime host >"$tmp/workflow-exec.json"

python3 - "$tmp/workflow-exec.json" "$tmp/agent-system" <<'PY'
import json
import sys
from pathlib import Path

payload = json.load(open(sys.argv[1], encoding="utf-8"))
root = Path(sys.argv[2])
assert payload["status"] == "completed", payload
assert payload["task_status"] == "completed", payload
assert payload["execution"]["status"] == "completed", payload
artifact = root / payload["execution"]["artifact"]
assert artifact.exists(), payload
run = json.load(open(root / "runs" / payload["run_id"] / "run.json", encoding="utf-8"))
task = json.load(open(root / "tasks" / f"{payload['task_id']}.json", encoding="utf-8"))
assert run["status"] == "completed", run
assert task["status"] == "completed", task
assert all(stage["status"] == "completed" for stage in run["stages"].values()), run["stages"]
print("workflow-execute-smoke-ok")
PY
