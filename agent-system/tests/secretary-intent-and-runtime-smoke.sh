#!/usr/bin/env bash
set -euo pipefail

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

cp -a "$SOURCE_ROOT/agent-system" "$tmp/agent-system"
export DIGITAL_OFFICE_SYSTEM_HOME="$tmp/agent-system"
export DIGITAL_OFFICE_CODEX_COMMAND="/bin/echo"
export DIGITAL_OFFICE_CLAUDE_CODE_COMMAND="/bin/echo"

office="$tmp/agent-system/bin/office-system.py"
gateway="$tmp/agent-system/bin/model-gateway"

"$office" secretary-chat --message "hello" --user smoke --role owner >"$tmp/hello.json"
python3 - "$tmp/hello.json" "$tmp/agent-system" <<'PY'
import json
import sys
from pathlib import Path

data = json.load(open(sys.argv[1], encoding="utf-8"))
root = Path(sys.argv[2])
assert data["status"] == "chat", data
assert data["should_create_project"] is False, data
assert data["intent"] == "greeting", data
assert not (root / "projects" / "hello").exists()
PY

"$office" secretary-chat --message "帮我新建一个合同审查项目" --user smoke --role owner >"$tmp/project-suggestion.json"
python3 - "$tmp/project-suggestion.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
assert data["status"] == "suggest_project", data
assert data["should_create_project"] is True, data
assert "start_project_intake" in data["next_actions"], data
PY

"$office" feedback-record \
  --feedback-type intent_misread \
  --scope global \
  --user-feedback "秘书误把问候当项目" \
  --correction "普通问候必须按聊天处理，不得创建项目" \
  --created-by smoke \
  --role owner >"$tmp/feedback.json"
"$office" feedback-list --scope global >"$tmp/feedback-list.json"
python3 - "$tmp/feedback.json" "$tmp/feedback-list.json" <<'PY'
import json
import sys

feedback = json.load(open(sys.argv[1], encoding="utf-8"))
items = json.load(open(sys.argv[2], encoding="utf-8"))
assert feedback["feedback"]["promotion_stage"] in {"tentative", "pending_confirmation", "confirmed_by_user"}, feedback
assert items["feedback"] and items["feedback"][0]["feedback_type"] == "intent_misread", items
PY

"$gateway" status >"$tmp/model-status.json"
python3 - "$tmp/model-status.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
runtimes = {item["id"]: item for item in data["local_runtimes"]}
assert runtimes["codex"]["ready"] is True, runtimes
assert runtimes["claude_code"]["ready"] is True, runtimes
PY

"$gateway" runtime-set --confirmed \
  --preferred-local-runtime codex \
  --agents-json '{"secretary":{"mode":"host","local_runtime":"codex","provider":"","model":""}}' >"$tmp/runtime.json"
python3 - "$tmp/runtime.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
runtime = data["runtime"]
assert runtime["preferred_local_runtime"] == "codex", runtime
assert runtime["agents"]["secretary"]["local_runtime"] == "codex", runtime
PY

"$gateway" resolve --agent secretary >"$tmp/resolve.json"
python3 - "$tmp/resolve.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
execution = data["execution"]
assert execution["mode"] == "host", execution
assert execution["local_runtime"]["id"] == "codex", execution
PY

echo "secretary-intent-and-runtime-smoke-ok"
