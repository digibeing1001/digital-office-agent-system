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
python3 -m py_compile agent-system/bin/office-system.py agent-system/bin/harness-check agent-system/bin/harness-runner scripts/agent-router
for file in $(git ls-files "*.json"); do
  python3 -m json.tool "$file" >/dev/null
done
git diff --check
python3 - <<'PY'
from pathlib import Path

critical_files = [
    "SOUL.md",
    "README.md",
    "README.zh-CN.md",
    "agent-system/ai-native-loop.manifest.json",
    "agent-system/agent-requests/config.example.json",
    "agent-system/agents.registry.json",
    "agent-system/harness/production-gates.json",
    "agent-system/secretary.capabilities.json",
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
grep -q "## Boundary And Pushback" SOUL.md || fail "default secretary SOUL missing pushback boundary"
grep -q "## Reflective Advisory Mode" SOUL.md || fail "default secretary SOUL missing reflective advisory mode"
grep -q "## Agent Routing And Workflow Orchestration" SOUL.md || fail "default secretary SOUL missing routing orchestration rules"
json_assert agent-system/secretary.capabilities.json 'data["persona_policy"]["default_stance"].startswith("Act as a capable digital chief of staff")'
json_assert agent-system/secretary.capabilities.json '"reflective_pushback" in [item["id"] for item in data["core_capabilities"]]'
json_assert agent-system/secretary.capabilities.json '"ai_native_loop_governance" in [item["id"] for item in data["core_capabilities"]]'
json_assert agent-system/secretary.capabilities.json 'data["ai_native_loop_policy"]["iteration_confirmation_required"] is True'
json_assert agent-system/secretary.capabilities.json 'data["routing_orchestration_policy"]["role_first_rule"].startswith("Select the needed orchestration role first")'
json_assert agent-system/secretary.capabilities.json 'data["production_harness_policy"]["role_skill_map"]["implementation"] == "vibe-coding-production-harness"'
json_assert agent-system/agents.registry.json '"vibe-coding-production-harness" in data["agents"]["coder"]["skills"]'
json_assert agent-system/agents.registry.json '"vibe-design-production-harness" in data["agents"]["vibe-designer"]["skills"]'
json_assert agent-system/harness/production-gates.json 'data["role_gates"]["implementation"]["minimum_gates"][0] == "build_or_compile_passes"'
json_assert agent-system/harness/tasks/vibe-coding-production.json 'data["task_id"] == "vibe-coding-production"'
json_assert agent-system/harness/tasks/vibe-design-production.json 'data["task_id"] == "vibe-design-production"'
json_assert agent-system/harness/tasks/portable-routing-production.json 'data["task_id"] == "portable-routing-production"'
json_assert agent-system/harness/tasks/ai-native-loop-production.json 'data["task_id"] == "ai-native-loop-production"'
json_assert agent-system/ai-native-loop.manifest.json 'data["stages"]["iterate"]["gates"][0] == "no_auto_iteration_without_user_confirmation"'
json_assert agent-system/ai-native-loop.manifest.json '"silent self-iteration" in data["stages"]["iterate"]["forbidden"]'
test -f skills/vibe-coding-production-harness/SKILL.md || fail "missing vibe coding harness skill"
test -f skills/vibe-design-production-harness/SKILL.md || fail "missing vibe design harness skill"

./install.sh "$WORK_DIR/hermes" >/dev/null
HOME_DIR="$WORK_DIR/hermes"
ROUTER="$HOME_DIR/scripts/agent-router"
OFFICE="$HOME_DIR/agent-system/bin/office-system"

"$ROUTER" --health >/dev/null
"$OFFICE" health >/dev/null
"$HOME_DIR/agent-system/bin/harness-check" >/dev/null
"$HOME_DIR/agent-system/bin/harness-runner" --task all --no-write >/dev/null
"$HOME_DIR/agent-system/bin/product-update" status >/dev/null

[ -f "$HOME_DIR/SOUL.md" ] || fail "default SOUL.md missing"
[ ! -e "$HOME_DIR/profiles/secretary" ] || fail "secretary profile must not be duplicated"
grep -q "## Boundary And Pushback" "$HOME_DIR/SOUL.md" || fail "installed secretary SOUL missing pushback boundary"
grep -q "## Reflective Advisory Mode" "$HOME_DIR/SOUL.md" || fail "installed secretary SOUL missing reflective advisory mode"
grep -q "## Agent Routing And Workflow Orchestration" "$HOME_DIR/SOUL.md" || fail "installed secretary SOUL missing routing orchestration rules"
grep -q "## AI Native Product Loop" "$HOME_DIR/SOUL.md" || fail "installed secretary SOUL missing AI native loop rules"

"$OFFICE" loop-start --run-id smoke-loop --task "Build a governed AI native product loop" >"$WORK_DIR/loop-start.json"
json_assert "$WORK_DIR/loop-start.json" 'data["run_id"] == "smoke-loop" and data["status"] == "created"'
"$OFFICE" loop-stage --run-id smoke-loop --stage perceive --status started --summary "Context gathered" >"$WORK_DIR/loop-stage.json"
json_assert "$WORK_DIR/loop-stage.json" 'data["run_id"] == "smoke-loop" and data["stage"] == "perceive" and data["run_status"] == "perceiving"'
"$OFFICE" iteration-proposal-create --title "Tighten smoke loop gate" --target harness --summary "Add a regression gate after reflection" --body "Add a harness check after reflection." --expected-impact "Fewer workflow drifts" --risk "Could slow delivery" --rollback "Remove the proposed gate" --run-id smoke-loop --regression-check "harness-runner --task all --no-write" >"$WORK_DIR/iteration-proposal.json"
proposal_id="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["proposal_id"])' "$WORK_DIR/iteration-proposal.json")"
must_fail "$OFFICE" iteration-proposal-apply --proposal-id "$proposal_id"
"$OFFICE" iteration-proposal-decision --proposal-id "$proposal_id" --decision tune --message "Need clearer risk" >"$WORK_DIR/iteration-tune.json"
json_assert "$WORK_DIR/iteration-tune.json" 'data["status"] == "needs_tuning"'
must_fail "$OFFICE" iteration-proposal-apply --proposal-id "$proposal_id" --confirmed
"$OFFICE" iteration-proposal-decision --proposal-id "$proposal_id" --decision confirm --message "User confirmed" >"$WORK_DIR/iteration-confirm.json"
json_assert "$WORK_DIR/iteration-confirm.json" 'data["status"] == "confirmed_for_application"'
"$OFFICE" iteration-proposal-apply --proposal-id "$proposal_id" --confirmed --regression-result "harness passed" --artifact "agent-system/harness/tasks/ai-native-loop-production.json" >"$WORK_DIR/iteration-apply.json"
json_assert "$WORK_DIR/iteration-apply.json" 'data["status"] == "applied_verified"'

HERMES_HOME="$HOME_DIR" "$ROUTER" --route-json "hello there" >"$WORK_DIR/route-fallback.json"
json_assert "$WORK_DIR/route-fallback.json" 'data["agent"] == "secretary" and data["profile"] == "__default__" and data.get("fallback") is True and data.get("clarification_required") is True'

HERMES_HOME="$HOME_DIR" "$ROUTER" --route-json "please debug this bug" >"$WORK_DIR/route-coder.json"
json_assert "$WORK_DIR/route-coder.json" 'data["agent"] == "coder" and data["workflow"] == "single" and data["confidence"] == "high"'

HERMES_HOME="$HOME_DIR" "$ROUTER" --route-json "先调研竞品，再规划数字办公室的产品方案" >"$WORK_DIR/route-research-plan.json"
json_assert "$WORK_DIR/route-research-plan.json" 'data["agent"] == "planer" and data["workflow"] == "research_then_plan" and data["steps"] == ["researcher", "planer"] and data["workflow_reason"]["source"] == "workflow_route"'

HERMES_HOME="$HOME_DIR" "$ROUTER" --route-json "先做市场调研，再判断这个产品该不该做和路线图" >"$WORK_DIR/route-research-pm.json"
json_assert "$WORK_DIR/route-research-pm.json" 'data["agent"] == "pm" and data["workflow"] == "research_then_pm" and data["steps"] == ["researcher", "pm"]'

HERMES_HOME="$HOME_DIR" "$ROUTER" --route-json "先明确产品需求，再做拟态 GUI 设计" >"$WORK_DIR/route-pm-design.json"
json_assert "$WORK_DIR/route-pm-design.json" 'data["agent"] == "vibe-designer" and data["workflow"] == "pm_to_design" and data["steps"] == ["pm", "vibe-designer"]'

HERMES_HOME="$HOME_DIR" "$ROUTER" --route-json "先梳理产品需求，再设计界面，最后实现前端原型代码" >"$WORK_DIR/route-end-to-end.json"
json_assert "$WORK_DIR/route-end-to-end.json" 'data["agent"] == "coder" and data["workflow"] == "pm_to_design_to_code" and data["steps"] == ["pm", "vibe-designer", "coder"]'

HERMES_HOME="$HOME_DIR" "$ROUTER" --agent coder --route-json "先调研竞品，再规划数字办公室的产品方案" >"$WORK_DIR/route-explicit-coder.json"
json_assert "$WORK_DIR/route-explicit-coder.json" 'data["agent"] == "coder" and data["workflow_reason"]["source"] == "agent_default"'

cat >"$WORK_DIR/portable-registry.json" <<'EOF'
{
  "version": "1.0.0",
  "kind": "portable-agent-registry",
  "defaults": {
    "fallback_agent": "frontdesk",
    "fallback_profile": "__default__",
    "fallback_model": "model-a",
    "fallback_provider": "provider-a",
    "memory_policy": "keymemory"
  },
  "routing_policy": {
    "minimum_score": 4,
    "ambiguity_margin": 2,
    "candidate_limit": 3,
    "workflow_minimum_score": 6
  },
  "orchestration_roles": {
    "intake": {"preferred_agents": ["frontdesk"]},
    "evidence": {"preferred_agents": ["domain-evidence"]},
    "implementation": {"preferred_agents": ["builder"]}
  },
  "workflows": {
    "evidence_to_execution": {
      "label": "Evidence to execution",
      "steps": ["@role:evidence", "@role:implementation"],
      "handoff_contract": "Evidence Agent verifies; implementation Agent executes."
    },
    "single": {
      "label": "Single specialist",
      "steps": ["{primary_agent}"],
      "handoff_contract": "Handle within boundary."
    }
  },
  "workflow_routes": [
    {
      "workflow": "evidence_to_execution",
      "primary_role": "implementation",
      "priority": 10,
      "minimum_score": 6,
      "match_all": [
        [{"term": "verify", "weight": 3}, {"term": "evidence", "weight": 3}],
        [{"term": "execute", "weight": 3}, {"term": "build", "weight": 3}]
      ]
    }
  ],
  "agents": {
    "frontdesk": {
      "display_name": "Frontdesk",
      "portable_role": "office-intake",
      "profile": "__default__",
      "model": "model-a",
      "provider": "provider-a",
      "memory_policy": "keymemory",
      "orchestration_roles": ["intake"],
      "routing": {"priority": 100, "default_workflow": "single", "keywords": [{"term": "clarify", "weight": 5}]}
    },
    "domain-evidence": {
      "display_name": "Domain Evidence",
      "portable_role": "domain-evidence",
      "profile": "__default__",
      "model": "model-b",
      "provider": "provider-b",
      "memory_policy": "keymemory",
      "orchestration_roles": ["evidence"],
      "routing": {"priority": 40, "default_workflow": "single", "keywords": [{"term": "verify", "weight": 5}]}
    },
    "builder": {
      "display_name": "Builder",
      "portable_role": "execution",
      "profile": "__default__",
      "model": "model-c",
      "provider": "provider-c",
      "memory_policy": "keymemory",
      "orchestration_roles": ["implementation"],
      "routing": {"priority": 50, "default_workflow": "single", "keywords": [{"term": "execute", "weight": 5}]}
    }
  },
  "route_tests": []
}
EOF
HERMES_HOME="$HOME_DIR" HERMES_AGENT_REGISTRY="$WORK_DIR/portable-registry.json" "$ROUTER" --route-json "verify the evidence then execute the build" >"$WORK_DIR/route-portable.json"
json_assert "$WORK_DIR/route-portable.json" 'data["agent"] == "builder" and data["workflow"] == "evidence_to_execution" and data["steps"] == ["domain-evidence", "builder"] and data["workflow_reason"]["primary_role"] == "implementation"'

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
