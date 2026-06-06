#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

must_fail() {
  set +e
  "$@" >"$WORK_DIR/must_fail.out" 2>"$WORK_DIR/must_fail.err"
  local code=$?
  set -e
  if [ "$code" -eq 0 ]; then
    echo "Command unexpectedly succeeded:" >&2
    printf '  %q' "$@" >&2
    echo >&2
    cat "$WORK_DIR/must_fail.out" >&2 || true
    cat "$WORK_DIR/must_fail.err" >&2 || true
    exit 1
  fi
}

json_assert() {
  local file="$1"
  local expr="$2"
  python3 - "$file" "$expr" <<'PY'
import json
import sys

path, expr = sys.argv[1], sys.argv[2]
with open(path, "r", encoding="utf-8") as handle:
    data = json.load(handle)
if not eval(expr, {"__builtins__": {"len": len}}, {"data": data}):
    raise SystemExit(f"assertion failed: {expr}\n{json.dumps(data, ensure_ascii=False, indent=2)}")
PY
}

cp -a "$REPO_ROOT" "$WORK_DIR/repo"
cd "$WORK_DIR/repo"

bash -n agent-system/tests/smoke.sh
python3 -m py_compile agent-system/bin/office-system.py scripts/agent-router
for file in $(git ls-files "*.json"); do
  python3 -m json.tool "$file" >/dev/null
done
git diff --check
python3 - <<'PY'
from pathlib import Path

critical_files = [
    "README.zh-CN.md",
    "agent-system/agent-requests/config.example.json",
    "agent-system/agents.registry.json",
    "agent-system/bin/office-system.py",
    "agent-system/docs/gui-contract.md",
]
markers = ["\u00c3", "\u00e6", "\u00e7", "\ufffd"]
bad = []
for name in critical_files:
    text = Path(name).read_text(encoding="utf-8")
    if any(marker in text for marker in markers):
        bad.append(name)
if bad:
    raise SystemExit("mojibake markers found in critical files: " + ", ".join(bad))
PY

./install.sh "$WORK_DIR/hermes" >/dev/null
HOME_DIR="$WORK_DIR/hermes"
ROUTER="$HOME_DIR/scripts/agent-router"
OFFICE="$HOME_DIR/agent-system/bin/office-system"

"$ROUTER" --health >/dev/null
"$OFFICE" health >/dev/null
"$HOME_DIR/agent-system/bin/product-update" status >/dev/null

[ -f "$HOME_DIR/SOUL.md" ] || fail "default SOUL.md missing"
[ ! -e "$HOME_DIR/profiles/secretary" ] || fail "secretary profile must not be duplicated"

HERMES_HOME="$HOME_DIR" "$ROUTER" --route-json "hello there" >"$WORK_DIR/route-fallback.json"
json_assert "$WORK_DIR/route-fallback.json" 'data["agent"] == "secretary" and data["profile"] == "__default__" and data.get("fallback") is True'

HERMES_HOME="$HOME_DIR" "$ROUTER" --route-json "please debug this bug" >"$WORK_DIR/route-coder.json"
json_assert "$WORK_DIR/route-coder.json" 'data["agent"] == "coder"'

"$OFFICE" project-create --project p1 --name "Project One" --agents pm,coder >/dev/null
must_fail "$OFFICE" project-create --project bad --name "Bad Project" --agents unknown-agent

"$OFFICE" knowledge-add-text --scope project --project p1 --title draft --body "alpha beta gamma" >"$WORK_DIR/kb-pending.json"
"$OFFICE" rag-index --scope project --project p1 --mode lexical >"$WORK_DIR/rag-pending.json"
json_assert "$WORK_DIR/rag-pending.json" 'data["chunks"] == 0'

"$OFFICE" knowledge-add-text --scope project --project p1 --title approved --body "alpha beta gamma" --approve >"$WORK_DIR/kb-approved.json"
"$OFFICE" rag-index --scope project --project p1 --mode lexical >"$WORK_DIR/rag-approved.json"
json_assert "$WORK_DIR/rag-approved.json" 'data["chunks"] > 0'
"$OFFICE" rag-search --scope project --project p1 --query beta >"$WORK_DIR/rag-search.json"
json_assert "$WORK_DIR/rag-search.json" 'len(data["results"]) > 0'

draft_path="$("$OFFICE" methodology-draft --project p1)"
must_fail "$OFFICE" methodology-approve --project p1 --draft "$draft_path"
"$OFFICE" methodology-approve --project p1 --draft "$draft_path" --confirmed >/dev/null

must_fail "$OFFICE" rule-add --scope agent --agent "../escape" --title bad --body bad
must_fail "$OFFICE" relay-add --project p1 --agent unknown-agent --title bad --body bad
must_fail "$OFFICE" agent-improvement-draft --agent pm --kind soul --title bad --body "please add skill"
must_fail "$OFFICE" agent-improvement-draft --agent pm --kind soul --title bad --body "please install a new skill"
must_fail "$OFFICE" agent-improvement-draft --agent pm --kind soul --title bad --body "please 新增 skill"

must_fail "$OFFICE" knowledge-source-mount --source-class provider_sold_industry_kb --source-id law-pack --tenant tenant-a --deployment dep-a --created-by user-a --mount-target project_knowledge --project p1 --entitlement ent-a
must_fail "$OFFICE" knowledge-source-mount --source-class provider_sold_industry_kb --source-id law-pack --tenant tenant-a --deployment dep-a --created-by user-a --mount-target licensed_project_reference --entitlement ent-a
"$OFFICE" knowledge-source-mount --source-class provider_sold_industry_kb --source-id law-pack --tenant tenant-a --deployment dep-a --created-by user-a --mount-target licensed_project_reference --project p1 --entitlement ent-a --knowledge-placeholder ignored --mount-id law-mount 2>/dev/null && fail "unexpected unsupported argument accepted" || true
"$OFFICE" knowledge-source-mount --source-class provider_sold_industry_kb --source-id law-pack --tenant tenant-a --deployment dep-a --created-by user-a --mount-target licensed_project_reference --project p1 --entitlement ent-a --mount-id law-mount --allowed-user user-a --allowed-role admin >"$WORK_DIR/mount.json"
json_assert "$WORK_DIR/mount.json" 'data["inside_digital_office_only"] is True and data["download_allowed"] is False and data["export_allowed"] is False'
must_fail "$OFFICE" knowledge-access-log --tenant tenant-a --deployment dep-a --user user-a --role admin --project p1 --source-class provider_sold_industry_kb --source-id law-pack --mount-id missing --knowledge-pack law-pack --entitlement ent-a --decision allow
must_fail "$OFFICE" knowledge-access-log --tenant tenant-a --deployment dep-a --user user-a --role admin --project p1 --source-class provider_sold_industry_kb --source-id law-pack --mount-id law-mount --knowledge-pack law-pack --decision allow
must_fail "$OFFICE" knowledge-access-log --tenant tenant-a --deployment dep-a --user user-a --role admin --project p1 --source-class provider_sold_industry_kb --source-id law-pack --mount-id law-mount --knowledge-pack other-pack --entitlement ent-a --decision allow
must_fail "$OFFICE" knowledge-access-log --tenant tenant-a --deployment dep-a --user user-b --role admin --project p1 --source-class provider_sold_industry_kb --source-id law-pack --mount-id law-mount --knowledge-pack law-pack --entitlement ent-a --decision allow
"$OFFICE" knowledge-access-log --tenant tenant-a --deployment dep-a --user user-a --role admin --project p1 --source-class provider_sold_industry_kb --source-id law-pack --mount-id law-mount --knowledge-pack law-pack --entitlement ent-a --query "contract" --result-source-id law-001 --snippet-count 1 --decision allow >"$WORK_DIR/access.json"
json_assert "$WORK_DIR/access.json" 'data["query_hash"] and data["result_source_ids"] == ["law-001"]'

"$OFFICE" agent-request-submit --title "Need QA" --body "Need a QA Agent" --project p1 --requested-by user-a --confirmed >"$WORK_DIR/request.json"
json_assert "$WORK_DIR/request.json" 'data["status_label"] == "\u63a5\u6536\u9700\u6c42"'

PLUGIN="$WORK_DIR/plugin"
mkdir -p "$PLUGIN/profiles/qa-agent"
cat >"$PLUGIN/profiles/qa-agent/SOUL.md" <<'EOF'
# QA Agent
EOF
cat >"$PLUGIN/agent-plugin.json" <<'EOF'
{
  "agent_id": "qa",
  "display_name": "QA Agent",
  "registry_entry": {
    "id": "qa",
    "display_name": "QA Agent",
    "portable_role": "quality-assurance-specialist",
    "profile": "qa-agent",
    "model": "MiniMax-M3",
    "provider": "minimax-cn",
    "memory_policy": "keymemory",
    "routing": {
      "priority": 10,
      "default_workflow": "single",
      "keywords": [
        {"term": "qa-test-token", "weight": 20}
      ]
    },
    "skills": []
  },
  "route_tests": [
    {"prompt": "qa-test-token", "expect": "qa"}
  ]
}
EOF

must_fail "$OFFICE" agent-plugin-report --package "$PLUGIN" --project missing-project
"$OFFICE" agent-plugin-report --package "$PLUGIN" --project p1 --request-id req1 >/dev/null
report_id="$(find "$HOME_DIR/agent-system/agent-plugins/status" -name '*.json' -printf '%f\n' | sed 's/\.json$//' | head -n 1)"
[ -n "$report_id" ] || fail "plugin report id not found"
must_fail "$OFFICE" agent-plugin-activate --package "$PLUGIN" --project p1 --request-id req1 --confirmed
must_fail "$OFFICE" agent-plugin-activate --package "$PLUGIN" --report-id "$report_id" --project p1 --request-id req1 --confirmed
"$OFFICE" agent-plugin-decision --report-id "$report_id" --decision tune --message "needs change" >/dev/null
must_fail "$OFFICE" agent-plugin-activate --package "$PLUGIN" --report-id "$report_id" --project p1 --request-id req1 --confirmed
"$OFFICE" agent-plugin-decision --report-id "$report_id" --decision confirm >/dev/null
must_fail "$OFFICE" agent-plugin-activate --package "$PLUGIN" --report-id "$report_id" --request-id req1 --confirmed
must_fail "$OFFICE" agent-plugin-activate --package "$PLUGIN" --report-id "$report_id" --project p1 --confirmed
must_fail "$OFFICE" agent-plugin-activate --package "$PLUGIN" --report-id "$report_id" --project p1 --request-id wrong-req --confirmed
BAD_PLUGIN="$WORK_DIR/bad-plugin"
mkdir -p "$BAD_PLUGIN/profiles/wrong-agent"
cat >"$BAD_PLUGIN/profiles/wrong-agent/SOUL.md" <<'EOF'
# Wrong Agent
EOF
cat >"$BAD_PLUGIN/agent-plugin.json" <<'EOF'
{
  "agent_id": "wrong",
  "display_name": "Wrong Agent",
  "registry_entry": {
    "id": "wrong",
    "display_name": "Wrong Agent",
    "portable_role": "wrong-agent",
    "profile": "wrong-agent",
    "model": "MiniMax-M3",
    "provider": "minimax-cn",
    "memory_policy": "keymemory",
    "routing": {
      "priority": 10,
      "default_workflow": "single",
      "keywords": [
        {"term": "wrong-test-token", "weight": 20}
      ]
    },
    "skills": []
  }
}
EOF
must_fail "$OFFICE" agent-plugin-activate --package "$BAD_PLUGIN" --report-id "$report_id" --project p1 --request-id req1 --confirmed
"$OFFICE" agent-plugin-activate --package "$PLUGIN" --report-id "$report_id" --project p1 --request-id req1 --confirmed >"$WORK_DIR/plugin-activated.json"
json_assert "$WORK_DIR/plugin-activated.json" 'data["agent_id"] == "qa" and data["router_health"] == "passed"'
HERMES_HOME="$HOME_DIR" "$ROUTER" --route-json "qa-test-token" >"$WORK_DIR/route-qa.json"
json_assert "$WORK_DIR/route-qa.json" 'data["agent"] == "qa"'
must_fail "$OFFICE" agent-plugin-activate --package "$PLUGIN" --report-id "$report_id" --project p1 --request-id req1 --confirmed

echo "smoke-ok"
