#!/usr/bin/env bash
set -euo pipefail
SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cp -a "$SOURCE_ROOT/agent-system" "$tmp/agent-system"
cp -a "$SOURCE_ROOT/scripts" "$tmp/scripts"
export DIGITAL_OFFICE_SYSTEM_HOME="$tmp/agent-system"
office="$tmp/agent-system/bin/office-system"
"$office" project-create --project intake-test --name "测试项目" --guided-intake --brief "为客户准备合规方案" >/dev/null
set +e
"$office" workflow-start --tenant t1 --deployment d1 --user u1 --role owner --project intake-test --task "开始执行" >"$tmp/blocked.json"
code=$?
set -e
test "$code" -eq 4
python3 - "$tmp/blocked.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
assert d["status"] == "needs_context"
assert len(d["context_readiness"]["suggestions"]) >= 3
assert d["context_readiness"]["question_policy"]["method"] == "first_principles_socratic"
assert "intent_confirmation_required" in d["context_readiness"]["blockers"]
PY
status_json="$tmp/status.json"
"$office" project-context-status --project intake-test >"$status_json"
intent_hash="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["intent"]["hash"])' "$status_json")"
"$office" project-intent-confirm --project intake-test --expected-hash "$intent_hash" --confirmed-by u1 --confirmed >/dev/null
"$office" project-context-update --project intake-test --updated-by u1 --context-json '{"deliverables":["合规方案"],"acceptance_criteria":["通过法务复核"],"constraints":["不得泄露客户数据"],"source_refs":["客户原始合同"],"stakeholders":["法务负责人"]}' >/dev/null
"$office" project-context-status --project intake-test >"$status_json"
python3 - "$status_json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
assert d["intent"]["confirmed"] is True
assert d["ready"] is True and d["confirmed"] is False
PY
"$office" project-context-confirm --project intake-test --confirmed-by u1 --confirmed >/dev/null
"$office" workflow-start --tenant t1 --deployment d1 --user u1 --role owner --project intake-test --task "开始执行" >"$tmp/run.json"
python3 - "$tmp/run.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
assert d["status"] in {"created", "blocked", "waiting_human_judgment"}
PY
echo "project-context-intake-smoke-ok"
