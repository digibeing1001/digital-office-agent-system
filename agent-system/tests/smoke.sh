#!/usr/bin/env bash
set -euo pipefail

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
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
if not eval(expr, {"__builtins__": {"all": all, "any": any, "len": len, "list": list, "set": set}}, {"data": data}):
    raise SystemExit(f"assertion failed: {expr}\n{json.dumps(data, ensure_ascii=False, indent=2)}")
PY
}

copy_required_path() {
  local path="$1"
  if [ ! -e "$SOURCE_ROOT/$path" ]; then
    fail "missing required installed path: $path"
  fi
  cp -a "$SOURCE_ROOT/$path" "$WORK_DIR/repo/"
}

clean_dir_keep_placeholder() {
  local path="$1"
  [ -d "$path" ] || mkdir -p "$path"
  find "$path" -mindepth 1 -maxdepth 1 ! -name ".gitignore" -exec rm -rf {} +
}

clean_runtime_state() {
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/approvals"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/judgments"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/logs"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/notifications"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/rule-proposals"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/runs"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/settings"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/tasks"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/agent-requests/outbox"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/agent-requests/status"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/data-sharing/exports"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/data-sharing/outbox"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/data-sharing/receipts"
  rm -f "$WORK_DIR/repo/agent-system/data-sharing/consent.json"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/harness/reports"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/iterations/applied"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/iterations/proposals"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/iterations/status"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/knowledge/company"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/knowledge/mounts"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/knowledge/spaces"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/models/cache"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/models/locks"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/rules/projects"
  clean_dir_keep_placeholder "$WORK_DIR/repo/agent-system/agent-improvements"
  find "$WORK_DIR/repo/agent-system/projects" -mindepth 1 -maxdepth 1 ! -name "_template" -exec rm -rf {} +
}

if [ -f "$SOURCE_ROOT/install.sh" ]; then
  SOURCE_MODE="repo"
  cp -a "$SOURCE_ROOT" "$WORK_DIR/repo"
else
  SOURCE_MODE="install"
  mkdir -p "$WORK_DIR/repo"
  copy_required_path "SOUL.md"
  copy_required_path "README.md"
  copy_required_path "README.zh-CN.md"
  copy_required_path "digital-office-gui"
  copy_required_path "agent-system"
  if [ ! -f "$SOURCE_ROOT/scripts/agent-router" ]; then
    fail "missing required installed script: scripts/agent-router"
  fi
  mkdir -p "$WORK_DIR/repo/scripts"
  cp -a "$SOURCE_ROOT/scripts/agent-router" "$WORK_DIR/repo/scripts/"
  copy_required_path "profiles"
  mkdir -p "$WORK_DIR/repo/skills"
  for skill in vibe-coding-production-harness vibe-design-production-harness; do
    if [ ! -d "$SOURCE_ROOT/skills/$skill" ]; then
      fail "missing required installed skill: $skill"
    fi
    cp -a "$SOURCE_ROOT/skills/$skill" "$WORK_DIR/repo/skills/"
  done
fi
clean_runtime_state
cd "$WORK_DIR/repo"

bash -n agent-system/tests/smoke.sh
bash -n agent-system/tests/web-pwa-smoke.sh
bash -n agent-system/tests/secretary-intent-and-runtime-smoke.sh
bash -n digital-office-gui
bash -n agent-system/bin/digital-office-gui
python3 -m py_compile agent-system/bin/office-system.py agent-system/bin/model-gateway agent-system/bin/harness-check agent-system/bin/harness-runner scripts/agent-router
python3 -m py_compile agent-system/bin/install-skill-sources
python3 agent-system/tests/model-gateway-smoke.py
bash agent-system/tests/secretary-intent-and-runtime-smoke.sh
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  json_files="$(git ls-files "*.json")"
else
  json_files="$(find agent-system scripts skills profiles -type f -name "*.json" | sort)"
fi
for file in $json_files; do
  python3 -m json.tool "$file" >/dev/null
done
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git diff --check
fi
python3 - <<'PY'
from pathlib import Path

critical_files = [
    "SOUL.md",
    "README.md",
    "README.zh-CN.md",
    "digital-office-gui",
    "agent-system/ai-native-loop.manifest.json",
    "agent-system/agent-requests/config.example.json",
    "agent-system/agents.registry.json",
    "agent-system/model-providers.registry.json",
    "agent-system/model-runtime.example.json",
    "agent-system/digital-employees.registry.json",
    "agent-system/workflow-packs.registry.json",
    "agent-system/context-envelope.schema.json",
    "agent-system/skill-installations.registry.json",
    "agent-system/coordination.policy.json",
    "agent-system/evals/runtime-replay-and-multilingual.json",
    "agent-system/host-injection.policy.json",
    "agent-system/judgment.policy.json",
    "agent-system/harness/production-gates.json",
    "agent-system/harness/tasks/runtime-replay-production.json",
    "agent-system/harness/tasks/multilingual-agent-eval-production.json",
    "agent-system/onboarding.presets.json",
    "agent-system/secretary.capabilities.json",
    "agent-system/bin/office-system.py",
    "agent-system/bin/model-gateway",
    "agent-system/tests/model-gateway-smoke.py",
    "agent-system/tests/secretary-intent-and-runtime-smoke.sh",
    "agent-system/harness/tasks/model-api-gateway-production.json",
    "agent-system/harness/tasks/project-context-intake-production.json",
    "agent-system/tests/project-context-intake-smoke.sh",
    "agent-system/bin/digital-office-gui",
    "agent-system/docs/gui-contract.md",
    "agent-system/docs/digital-lawyer.zh-CN.md",
    "agent-system/docs/ui-design-readiness.zh-CN.md",
    "agent-system/web/app/index.html",
    "agent-system/web/app/manifest.webmanifest",
    "agent-system/web/app/service-worker.js",
    "agent-system/tests/web-pwa-smoke.sh",
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
json_assert agent-system/onboarding.presets.json '"assistant_style" in data["fields"] and "neutral_operator" in data["fields"]["assistant_style"]["choices"]'
json_assert agent-system/secretary.capabilities.json 'data["persona_policy"]["default_stance"].startswith("Use the neutral operator baseline")'
json_assert agent-system/secretary.capabilities.json '"gui_settings_governance" in [item["id"] for item in data["core_capabilities"]]'
json_assert agent-system/secretary.capabilities.json '"web_ui_pwa_governance" in [item["id"] for item in data["core_capabilities"]]'
json_assert agent-system/secretary.capabilities.json 'data["gui_state_policy"]["home_snapshot_command"].startswith("office-system gui-state")'
json_assert agent-system/secretary.capabilities.json '"web_ui_pwa" in data["gui_state_policy"]["required_surfaces"]'
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
json_assert agent-system/harness/tasks/gui-readiness-production.json 'data["task_id"] == "gui-readiness-production"'
json_assert agent-system/harness/tasks/web-pwa-production.json 'data["task_id"] == "web-pwa-production"'
json_assert agent-system/harness/tasks/direct-agent-invocation-production.json 'data["task_id"] == "direct-agent-invocation-production"'
json_assert agent-system/harness/tasks/workflow-canvas-revision-production.json 'data["task_id"] == "workflow-canvas-revision-production"'
json_assert agent-system/harness/tasks/knowledge-space-acl-production.json 'data["task_id"] == "knowledge-space-acl-production"'
json_assert agent-system/harness/tasks/role-workbench-production.json 'data["task_id"] == "role-workbench-production"'
json_assert agent-system/harness/tasks/host-injection-production.json 'data["task_id"] == "host-injection-production"'
json_assert agent-system/harness/tasks/ppt-production.json 'data["task_id"] == "ppt-production"'
json_assert agent-system/harness/tasks/human-judgment-gate-production.json 'data["task_id"] == "human-judgment-gate-production"'
json_assert agent-system/harness/tasks/collaborative-rule-intake-production.json 'data["task_id"] == "collaborative-rule-intake-production"'
json_assert agent-system/harness/tasks/runtime-replay-production.json 'data["task_id"] == "runtime-replay-production"'
json_assert agent-system/harness/tasks/multilingual-agent-eval-production.json 'data["task_id"] == "multilingual-agent-eval-production"'
json_assert agent-system/harness/tasks/digital-lawyer-production.json 'data["task_id"] == "digital-lawyer-production"'
json_assert agent-system/harness/tasks/digital-employee-model-production.json 'data["task_id"] == "digital-employee-model-production"'
json_assert agent-system/harness/tasks/context-envelope-production.json 'data["task_id"] == "context-envelope-production"'
json_assert agent-system/harness/tasks/context-handoff-production.json 'data["task_id"] == "context-handoff-production"'
json_assert agent-system/harness/tasks/project-context-intake-production.json 'data["task_id"] == "project-context-intake-production"'
json_assert agent-system/harness/tasks/local-skill-installation-production.json 'data["task_id"] == "local-skill-installation-production"'
json_assert agent-system/harness/tasks/ui-design-readiness-production.json 'data["task_id"] == "ui-design-readiness-production"'
json_assert agent-system/digital-employees.registry.json 'data["model"]["levels"] == ["secretary_control_plane", "digital_employee_agents", "skill_staff_lanes"] and data["employees"]["legal"]["agent_id"] == "legal"'
json_assert agent-system/workflow-packs.registry.json 'data["packs"]["legal"]["owner_agent"] == "legal" and data["packs"]["legal"]["context_envelope_required"] is True'
json_assert agent-system/skill-installations.registry.json 'data["installations"]["claude-for-legal-zh"]["status"] == "installed_local" and data["installations"]["Legal-Skills-Chinese"]["status"] == "blocked_license"'
json_assert agent-system/context-envelope.schema.json 'data["properties"]["version"]["const"] == "2.0.0" and {"context_id","facts","omissions","context_budget","state_hash","artifact_refs","risk_flags"} <= set(data["required"])'
json_assert agent-system/context-handoff.policy.json 'data["default_mode"] == "hybrid" and set(data["acknowledgment"]["decisions"]) == {"accept","request_context","reject"}'
json_assert agent-system/judgment.policy.json '"regulated_professional_domain" in [item["id"] for item in data["categories"]]'
json_assert agent-system/coordination.policy.json '"parallel_expert_dag" in data["modes"] and "human_gated" in data["modes"]'
json_assert agent-system/evals/runtime-replay-and-multilingual.json 'len(data["cases"]) >= 6'
json_assert agent-system/host-injection.policy.json 'data["default_agent_role"] == "secretary" and data["supported_hosts"]["openclaw"]["default_agent_injection"] == "AGENTS.md"'
json_assert agent-system/ai-native-loop.manifest.json 'list(data["stages"]) == ["context","decide","act","evaluate"]'
json_assert agent-system/ai-native-loop.manifest.json 'set(data["controller"]["decisions"]) == {"continue","replan","retry","wait_human","complete","fail","cancel","budget_exhausted"}'
json_assert agent-system/ai-native-loop.manifest.json '"run_ledger" in data["stages"]["act"]["required_artifacts"]'
test -f skills/vibe-coding-production-harness/SKILL.md || fail "missing vibe coding harness skill"
test -f skills/vibe-design-production-harness/SKILL.md || fail "missing vibe design harness skill"
test -f skills/digital-lawyer-workflows/SKILL.md || fail "missing digital lawyer workflow skill"
test -f skills/_imported/claude-for-legal-ZH/.agents/skills/chinese-legal-commercial/SKILL.md || fail "missing local claude-for-legal-ZH source skill"

if [ "$SOURCE_MODE" = "repo" ]; then
  ./install.sh "$WORK_DIR/hermes" >/dev/null
  HOME_DIR="$WORK_DIR/hermes"
else
  HOME_DIR="$WORK_DIR/repo"
fi
ROUTER="$HOME_DIR/scripts/agent-router"
OFFICE="$HOME_DIR/agent-system/bin/office-system"
GUI="$HOME_DIR/digital-office-gui"
GUI_BIN="$HOME_DIR/agent-system/bin/digital-office-gui"

"$ROUTER" --health >/dev/null
"$GUI" --help >/dev/null
"$GUI_BIN" --help >/dev/null
"$HOME_DIR/agent-system/bin/install-skill-sources" >/dev/null
"$OFFICE" health >/dev/null
"$HOME_DIR/agent-system/bin/harness-check" >/dev/null
"$HOME_DIR/agent-system/bin/harness-runner" --task all --no-write >/dev/null
"$HOME_DIR/agent-system/bin/product-update" status >/dev/null
"$OFFICE" eval-run --suite runtime-replay-and-multilingual --no-write >"$WORK_DIR/runtime-eval.json"
json_assert "$WORK_DIR/runtime-eval.json" 'data["status"] == "success" and data["passed"] == data["total"]'
"$OFFICE" loop-start --run-id smoke-replay-run --agent writer --task "Draft a cited handoff summary." >"$WORK_DIR/smoke-loop.json"
"$OFFICE" checkpoint-create --run-id smoke-replay-run --checkpoint-id smoke-cp --stage context --label "smoke checkpoint" --resume-cursor context:ready --state-json '{"ok":true}' >"$WORK_DIR/smoke-checkpoint.json"
must_fail "$OFFICE" checkpoint-create --run-id smoke-replay-run --checkpoint-id smoke-human-cp-bad --stage decide --label "bad human checkpoint" --requires-human --reason "needs decision"
"$OFFICE" checkpoint-create --run-id smoke-replay-run --checkpoint-id smoke-human-cp --stage decide --label "human checkpoint" --requires-human --create-judgment --reason "needs decision" --created-by user-a --role project_manager >"$WORK_DIR/smoke-human-checkpoint.json"
json_assert "$WORK_DIR/smoke-human-checkpoint.json" 'data["checkpoint"]["requires_human"] is True and data["judgment_case"]["status"] == "pending"'
SMOKE_CONTEXT='{"kind":"digital-office-context-envelope","version":"2.0.0","context_id":"smoke-replay-run","run_id":"smoke-replay-run","task_id":"work-smoke-replay-run","context_version":1,"cycle_index":1,"from":{"type":"agent","id":"writer"},"to":{"type":"agent","id":"researcher"},"goal":"Return source-backed evidence.","user_intent":"Draft a cited handoff summary.","summary":"Evidence is required before drafting.","current_stage":"context","constraints":[],"acceptance_criteria":["Researcher provides source-backed evidence."],"facts":[],"source_refs":[],"artifact_refs":[],"decisions":[],"open_questions":[],"omissions":[],"risk_flags":[],"permissions":{"tenant_id":"t1","project_id":"p1","requested_by":"user-a","role":"project_manager","allowed_actions":["research"]},"context_budget":{"strategy":"hybrid","estimated_tokens":200,"max_tokens":1000,"compacted":false},"handoff_reason":"Need evidence before final draft.","state_hash":"0123456789abcdef"}'
"$OFFICE" handoff-create --run-id smoke-replay-run --handoff-id smoke-handoff --from-agent writer --to-agent researcher --stage context --reason "Need evidence before final draft." --input-schema-json '{"required":["sources"]}' --context-json "$SMOKE_CONTEXT" --acceptance-criterion "Researcher provides source-backed evidence." >"$WORK_DIR/smoke-handoff.json"
smoke_context_hash="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["context_hash"])' "$WORK_DIR/smoke-handoff.json")"
"$OFFICE" handoff-ack --run-id smoke-replay-run --handoff-id smoke-handoff --received-by researcher --decision accept --expected-context-hash "$smoke_context_hash" >"$WORK_DIR/smoke-handoff-ack.json"
json_assert "$WORK_DIR/smoke-handoff-ack.json" 'data["status"] == "accepted"'
"$OFFICE" run-ledger-list --run-id smoke-replay-run >"$WORK_DIR/smoke-ledger.json"
json_assert "$WORK_DIR/smoke-ledger.json" 'len(data["events"]) >= 3 and all(item.get("event_hash") for item in data["events"])'
"$OFFICE" coordination-plan --task "Compare independent examples in parallel before synthesis." --agent researcher --agent writer --parallelizable >"$WORK_DIR/smoke-coordination.json"
json_assert "$WORK_DIR/smoke-coordination.json" 'data["mode"] == "parallel_expert_dag"'

must_fail "$OFFICE" settings-status
"$OFFICE" onboarding-options >"$WORK_DIR/onboarding-options.json"
json_assert "$WORK_DIR/onboarding-options.json" 'data["configured"] is False and "work_mode" in data["presets"]["fields"]'
must_fail "$OFFICE" onboarding-apply --assistant-style warm_coordinator
"$OFFICE" onboarding-apply --assistant-style warm_coordinator --address-style friendly --language auto --initiative-level proactive_suggestions --pushback-style risk_based --approval-strictness strict --memory-mode personalized --work-mode balanced --company-name "Example Co" --secretary-name "Office Assistant" --confirmed >"$WORK_DIR/onboarding-apply.json"
json_assert "$WORK_DIR/onboarding-apply.json" 'data["source"] == "gui_first_run_onboarding" and data["choices"]["assistant_style"] == "warm_coordinator" and data["choices"]["approval_strictness"] == "strict"'
"$OFFICE" settings-update --work-mode quality --confirmed >"$WORK_DIR/settings-update.json"
json_assert "$WORK_DIR/settings-update.json" 'data["source"] == "gui_settings_update" and data["choices"]["work_mode"] == "quality" and data["choices"]["approval_strictness"] == "strict"'
"$OFFICE" settings-status >"$WORK_DIR/settings-status.json"
json_assert "$WORK_DIR/settings-status.json" 'data["configured"] is True and data["preferences"]["secretary_name"] == "Office Assistant"'
"$OFFICE" gui-state --user user-a --limit 5 >"$WORK_DIR/gui-state-initial.json"
json_assert "$WORK_DIR/gui-state-initial.json" 'data["settings"]["configured"] is True and "global_settings" in [item["id"] for item in data["capabilities"]] and "web_ui_pwa" in [item["id"] for item in data["capabilities"]] and "direct_agent_invocation" in [item["id"] for item in data["capabilities"]] and "knowledge_spaces" in [item["id"] for item in data["capabilities"]]'
bash "$HOME_DIR/agent-system/tests/web-pwa-smoke.sh" >"$WORK_DIR/web-pwa-smoke.log"

[ -f "$HOME_DIR/SOUL.md" ] || fail "default SOUL.md missing"
[ ! -e "$HOME_DIR/profiles/secretary" ] || fail "secretary profile must not be duplicated"
grep -q "## Boundary And Pushback" "$HOME_DIR/SOUL.md" || fail "installed secretary SOUL missing pushback boundary"
grep -q "## Reflective Advisory Mode" "$HOME_DIR/SOUL.md" || fail "installed secretary SOUL missing reflective advisory mode"
grep -q "## Agent Routing And Workflow Orchestration" "$HOME_DIR/SOUL.md" || fail "installed secretary SOUL missing routing orchestration rules"
grep -q "## AI Native Product Loop" "$HOME_DIR/SOUL.md" || fail "installed secretary SOUL missing AI native loop rules"

"$OFFICE" loop-start --run-id smoke-loop --task "Build a governed AI native product loop" >"$WORK_DIR/loop-start.json"
json_assert "$WORK_DIR/loop-start.json" 'data["run_id"] == "smoke-loop" and data["status"] == "created"'
"$OFFICE" loop-stage --run-id smoke-loop --stage context --status started --summary "Context gathered" >"$WORK_DIR/loop-stage.json"
json_assert "$WORK_DIR/loop-stage.json" 'data["run_id"] == "smoke-loop" and data["stage"] == "context" and data["run_status"] == "context_loading"'
"$OFFICE" iteration-proposal-create --title "Tighten smoke loop gate" --target harness --summary "Add a regression gate after evaluation" --body "Add a harness check after evaluation." --expected-impact "Fewer workflow drifts" --risk "Could slow delivery" --rollback "Remove the proposed gate" --run-id smoke-loop --regression-check "harness-runner --task all --no-write" >"$WORK_DIR/iteration-proposal.json"
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
json_assert "$WORK_DIR/route-research-plan.json" 'data["agent"] == "planner" and data["workflow"] == "research_then_plan" and data["steps"] == ["researcher", "planner"] and data["workflow_reason"]["source"] == "workflow_route"'

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

"$OFFICE" auth-decision --tenant tenant-a --deployment dep-a --user user-a --role project_manager --action workflow.start --resource-type workflow_run --resource-id planned-run --project p1 --agent coder >"$WORK_DIR/auth-allow.json"
json_assert "$WORK_DIR/auth-allow.json" 'data["allowed"] is True'
must_fail "$OFFICE" auth-decision --tenant tenant-a --deployment dep-a --user user-a --role viewer --action workflow.start --resource-type workflow_run --resource-id planned-run --project p1 --agent coder

"$OFFICE" workflow-start --tenant tenant-a --deployment dep-a --user user-a --role project_manager --project p1 --task "product requirement design ui prototype code implement frontend" --idempotency-key smoke-workflow >"$WORK_DIR/workflow-start.json"
json_assert "$WORK_DIR/workflow-start.json" 'data["status"] == "created" and data["task_status"] == "queued" and data["route"]["agent"] == "coder" and data["route"]["workflow"] == "pm_to_design_to_code"'
workflow_run="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["run_id"])' "$WORK_DIR/workflow-start.json")"
workflow_task="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["task_id"])' "$WORK_DIR/workflow-start.json")"
"$OFFICE" run-ledger-list --run-id "$workflow_run" >"$WORK_DIR/workflow-ledger.json"
json_assert "$WORK_DIR/workflow-ledger.json" 'any(item.get("event") == "workflow_started" and item.get("event_hash") for item in data["events"])'
"$OFFICE" workflow-start --tenant tenant-a --deployment dep-a --user user-a --role project_manager --project p1 --task "product requirement design ui prototype code implement frontend" --idempotency-key smoke-workflow >"$WORK_DIR/workflow-idempotent.json"
json_assert "$WORK_DIR/workflow-idempotent.json" 'data["idempotent"] is True and data["run"]["run_id"]'
"$OFFICE" workflow-list --project p1 >"$WORK_DIR/workflow-list.json"
json_assert "$WORK_DIR/workflow-list.json" 'len(data["runs"]) >= 1'
"$OFFICE" task-list --project p1 --status queued >"$WORK_DIR/task-list.json"
json_assert "$WORK_DIR/task-list.json" 'len(data["tasks"]) >= 1'

"$OFFICE" agent-invoke --tenant tenant-a --deployment dep-a --user user-a --role project_manager --project p1 --agent coder --task "direct backend implementation request" --run-id direct-run --task-id direct-task >"$WORK_DIR/direct-agent.json"
json_assert "$WORK_DIR/direct-agent.json" 'data["invocation_mode"] == "direct_agent" and data["agent_id"] == "coder" and data["workflow_run_id"] == "direct-run" and data["task_id"] == "direct-task" and data["authorization"]["allowed"] is True and data["audit_event_id"]'
"$OFFICE" run-ledger-list --run-id direct-run >"$WORK_DIR/direct-agent-ledger.json"
json_assert "$WORK_DIR/direct-agent-ledger.json" 'any(item.get("event") == "agent_invoked" and item.get("event_hash") for item in data["events"])'
must_fail "$OFFICE" agent-invoke --tenant tenant-a --deployment dep-a --user user-a --role viewer --project p1 --agent coder --task denied
must_fail "$OFFICE" agent-invoke --tenant tenant-a --deployment dep-a --user user-a --role project_manager --project p1 --agent researcher --task denied
must_fail "$OFFICE" agent-invoke --tenant tenant-a --deployment dep-a --user user-a --role project_manager --project p1 --agent unknown-agent --task denied
"$OFFICE" workflow-status --run-id direct-run >"$WORK_DIR/direct-run-status.json"
initial_revision="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["active_revision_id"])' "$WORK_DIR/direct-run-status.json")"
json_assert "$WORK_DIR/direct-run-status.json" 'data["invocation_mode"] == "direct_agent" and data["active_revision_id"] and data["tasks"] == ["direct-task"]'
"$OFFICE" workflow-draft-create --run-id direct-run --created-by user-a --role project_manager --revision-id invalid-draft >/dev/null
"$OFFICE" workflow-draft-patch --run-id direct-run --revision-id invalid-draft --updated-by user-a --role project_manager --patch-json '{"operations":[{"op":"remove_node","node_id":"final-output"}]}' >"$WORK_DIR/invalid-draft-patch.json"
"$OFFICE" workflow-draft-validate --run-id direct-run --revision-id invalid-draft >"$WORK_DIR/invalid-draft-validate.json"
json_assert "$WORK_DIR/invalid-draft-validate.json" 'data["validation"]["status"] == "invalid" and len(data["validation"]["errors"]) >= 1'
must_fail "$OFFICE" workflow-draft-activate --run-id direct-run --revision-id invalid-draft --activated-by user-a --role project_manager --confirmed
"$OFFICE" workflow-draft-create --run-id direct-run --created-by user-a --role project_manager --revision-id draft-1 >/dev/null
"$OFFICE" workflow-draft-patch --run-id direct-run --revision-id draft-1 --updated-by user-a --role project_manager --patch-json '{"operations":[{"op":"add_node","node":{"node_id":"approval-1","type":"approval_gate","title":"Approval"}},{"op":"remove_edge","from":"agent-1-coder","to":"final-output"},{"op":"add_edge","from":"agent-1-coder","to":"approval-1"},{"op":"add_edge","from":"approval-1","to":"final-output"}]}' >"$WORK_DIR/valid-draft-patch.json"
"$OFFICE" workflow-draft-validate --run-id direct-run --revision-id draft-1 >"$WORK_DIR/valid-draft-validate.json"
json_assert "$WORK_DIR/valid-draft-validate.json" 'data["validation"]["status"] == "valid"'
must_fail "$OFFICE" workflow-draft-activate --run-id direct-run --revision-id draft-1 --activated-by user-a --role project_manager
"$OFFICE" workflow-draft-activate --run-id direct-run --revision-id draft-1 --activated-by user-a --role project_manager --confirmed >"$WORK_DIR/draft-activate.json"
json_assert "$WORK_DIR/draft-activate.json" 'data["active_revision_id"] == "draft-1" and data["validation"]["status"] == "valid"'
"$OFFICE" workflow-node-context --run-id direct-run --node-id agent-1-coder >"$WORK_DIR/node-context.json"
json_assert "$WORK_DIR/node-context.json" 'data["active_revision_id"] == "draft-1" and data["node"]["agent_id"] == "coder" and "approval-1" in data["downstream_node_ids"]'
must_fail "$OFFICE" workflow-node-context --run-id direct-run --node-id agent-1-coder --revision-id "$initial_revision"
"$OFFICE" workflow-control --run-id direct-run --action pause --requested-by user-a --role project_manager >"$WORK_DIR/workflow-pause.json"
json_assert "$WORK_DIR/workflow-pause.json" 'data["status"] == "paused_after_current_node" and data["outcome"] == "pause_requested"'
"$OFFICE" workflow-control --run-id direct-run --action resume --requested-by user-a --role project_manager >"$WORK_DIR/workflow-runtime-resume.json"
json_assert "$WORK_DIR/workflow-runtime-resume.json" 'data["status"] == "context_loading"'
must_fail "$OFFICE" workflow-control --run-id direct-run --action stop --requested-by user-a --role project_manager
"$OFFICE" workflow-control --run-id direct-run --action stop --requested-by user-a --role project_manager --confirmed >"$WORK_DIR/workflow-stop.json"
json_assert "$WORK_DIR/workflow-stop.json" 'data["status"] == "stopped" and data["outcome"] == "stopped"'
"$OFFICE" task-status --task-id direct-task >"$WORK_DIR/direct-task-stopped.json"
json_assert "$WORK_DIR/direct-task-stopped.json" 'data["status"] == "cancelled"'

must_fail "$OFFICE" approval-create --tenant tenant-a --deployment dep-a --title "Approve smoke workflow" --action workflow.continue --resource-type workflow_run --resource-id "$workflow_run" --requested-by user-a --requested-by-role viewer --approver-role project_manager --project p1 --workflow-run "$workflow_run" --task-id "$workflow_task"
"$OFFICE" approval-create --tenant tenant-a --deployment dep-a --title "Approve smoke workflow" --action workflow.continue --resource-type workflow_run --resource-id "$workflow_run" --requested-by user-a --requested-by-role project_manager --approver-role project_manager --project p1 --workflow-run "$workflow_run" --task-id "$workflow_task" >"$WORK_DIR/approval-create.json"
approval_id="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["approval"]["approval_id"])' "$WORK_DIR/approval-create.json")"
"$OFFICE" task-status --task-id "$workflow_task" >"$WORK_DIR/task-waiting.json"
json_assert "$WORK_DIR/task-waiting.json" 'data["status"] == "waiting_approval"'
must_fail "$OFFICE" approval-decision --approval-id "$approval_id" --decision approve --decided-by user-a --role project_manager
"$OFFICE" approval-decision --approval-id "$approval_id" --decision approve --decided-by user-a --role project_manager --confirmed >"$WORK_DIR/approval-decision.json"
json_assert "$WORK_DIR/approval-decision.json" 'data["approval"]["status"] == "approved"'
"$OFFICE" workflow-status --run-id "$workflow_run" >"$WORK_DIR/workflow-approved.json"
json_assert "$WORK_DIR/workflow-approved.json" 'data["status"] == "context_loading"'
must_fail "$OFFICE" task-update --task-id "$workflow_task" --status completed --summary "viewer cannot complete" --updated-by user-a --role viewer
"$OFFICE" task-update --task-id "$workflow_task" --status completed --summary "workflow closed" --updated-by user-a --role project_manager >"$WORK_DIR/task-completed.json"
json_assert "$WORK_DIR/task-completed.json" 'data["status"] == "completed"'
"$OFFICE" workflow-status --run-id "$workflow_run" >"$WORK_DIR/workflow-completed.json"
json_assert "$WORK_DIR/workflow-completed.json" 'data["status"] == "blocked" and "stage_context_not_completed" in data["blockers"]'
"$OFFICE" audit-events --resource-type approval --resource-id "$approval_id" >"$WORK_DIR/audit-approval.json"
json_assert "$WORK_DIR/audit-approval.json" 'len(data["events"]) >= 1 and data["events"][-1]["event_hash"]'
"$OFFICE" notification-list --user user-a >"$WORK_DIR/notification-list.json"
json_assert "$WORK_DIR/notification-list.json" 'len(data["notifications"]) >= 1'
"$OFFICE" gui-state --user user-a --project p1 --limit 10 >"$WORK_DIR/gui-state-workflow.json"
json_assert "$WORK_DIR/gui-state-workflow.json" 'data["settings"]["configured"] is True and data["workflows"]["count"] >= 1 and data["workflows"]["draft_revision_count"] >= 1 and data["tasks"]["count"] >= 1 and data["approvals"]["count"] >= 1 and data["notifications"]["count"] >= 1'
"$OFFICE" workbench-state --tenant tenant-a --deployment dep-a --user user-a --role project_manager --project p1 >"$WORK_DIR/workbench-manager.json"
json_assert "$WORK_DIR/workbench-manager.json" 'data["view"] == "project_lead" and "team_tasks" in data["sections"]'
"$OFFICE" workbench-state --tenant tenant-a --deployment dep-a --user owner --role owner >"$WORK_DIR/workbench-owner.json"
json_assert "$WORK_DIR/workbench-owner.json" 'data["view"] == "owner_global" and "project_health" in data["sections"] and "system_health" in data["sections"]'
"$OFFICE" workbench-state --tenant tenant-a --deployment dep-a --user user-a --role member --project p1 >"$WORK_DIR/workbench-member.json"
json_assert "$WORK_DIR/workbench-member.json" 'data["view"] == "member" and "my_tasks" in data["sections"]'
"$OFFICE" workbench-state --tenant tenant-a --deployment dep-a --user user-a --role viewer --project p1 >"$WORK_DIR/workbench-viewer.json"
json_assert "$WORK_DIR/workbench-viewer.json" 'data["view"] == "viewer" and "visible_projects" in data["sections"]'

"$OFFICE" workflow-start --tenant tenant-a --deployment dep-a --user user-a --role project_manager --project p1 --task "hello there" >"$WORK_DIR/workflow-clarify.json"
clarify_run="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["run_id"])' "$WORK_DIR/workflow-clarify.json")"
clarify_case="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["judgment_case"]["case_id"])' "$WORK_DIR/workflow-clarify.json")"
json_assert "$WORK_DIR/workflow-clarify.json" 'data["status"] == "waiting_human_judgment" and data["route"]["agent"] == "secretary" and data["judgment_case"]["status"] == "pending"'
must_fail "$OFFICE" workflow-resume --run-id "$clarify_run" --requested-by user-a --role project_manager --reason "user clarified task"
"$OFFICE" judgment-decision --case-id "$clarify_case" --decision approve --decided-by user-a --role project_manager --confirmed --message "user clarified task" >"$WORK_DIR/judgment-clarify.json"
json_assert "$WORK_DIR/judgment-clarify.json" 'data["judgment"]["status"] == "approved"'
"$OFFICE" workflow-resume --run-id "$clarify_run" --requested-by user-a --role project_manager --reason "user clarified task" >"$WORK_DIR/workflow-resume.json"
json_assert "$WORK_DIR/workflow-resume.json" 'data["status"] == "context_loading"'
must_fail "$OFFICE" workflow-cancel --run-id "$clarify_run" --requested-by user-a --role project_manager --reason "stop"
"$OFFICE" workflow-cancel --run-id "$clarify_run" --requested-by user-a --role project_manager --reason "stop" --confirmed >"$WORK_DIR/workflow-cancel.json"
json_assert "$WORK_DIR/workflow-cancel.json" 'data["status"] == "cancelled"'

"$OFFICE" knowledge-add-text --scope project --project p1 --title draft --body "alpha beta gamma" >"$WORK_DIR/kb-pending.json"
"$OFFICE" rag-index --scope project --project p1 --mode lexical >"$WORK_DIR/rag-pending.json"
json_assert "$WORK_DIR/rag-pending.json" 'data["chunks"] == 0'

"$OFFICE" knowledge-add-text --scope project --project p1 --title approved --body "alpha beta gamma" --approve >"$WORK_DIR/kb-approved.json"
"$OFFICE" rag-index --scope project --project p1 --mode lexical >"$WORK_DIR/rag-approved.json"
json_assert "$WORK_DIR/rag-approved.json" 'data["chunks"] > 0'
"$OFFICE" rag-search --scope project --project p1 --query beta >"$WORK_DIR/rag-search.json"
json_assert "$WORK_DIR/rag-search.json" 'len(data["results"]) > 0'

"$OFFICE" knowledge-folder-create --space-type personal --owner alice --folder-id private --title Private --created-by alice --role member >"$WORK_DIR/knowledge-folder.json"
"$OFFICE" knowledge-item-add --space-type personal --owner alice --folder-id private --item-id item-1 --title Secret --source-ref local://secret.md --created-by alice --role member >"$WORK_DIR/knowledge-item.json"
must_fail "$OFFICE" knowledge-access-check --space-type personal --owner alice --resource-type item --resource-id item-1 --user bob --role member
"$OFFICE" knowledge-share --space-type personal --owner alice --resource-type folder --resource-id private --target-type user --target-id bob --shared-by alice --role member >"$WORK_DIR/knowledge-share-user.json"
"$OFFICE" knowledge-access-check --space-type personal --owner alice --resource-type item --resource-id item-1 --user bob --role member >"$WORK_DIR/knowledge-access-bob.json"
json_assert "$WORK_DIR/knowledge-access-bob.json" 'data["decision"]["allowed"] is True and data["decision"]["matched_shares"]'
must_fail "$OFFICE" knowledge-access-check --space-type personal --owner alice --resource-type item --resource-id item-1 --user worker --role member --agent coder
"$OFFICE" knowledge-share --space-type personal --owner alice --resource-type item --resource-id item-1 --target-type agent --target-id coder --shared-by alice --role member >"$WORK_DIR/knowledge-share-agent.json"
"$OFFICE" knowledge-access-check --space-type personal --owner alice --resource-type item --resource-id item-1 --user worker --role member --agent coder >"$WORK_DIR/knowledge-access-agent.json"
json_assert "$WORK_DIR/knowledge-access-agent.json" 'data["decision"]["allowed"] is True'
"$OFFICE" knowledge-scope-resolve --space-type personal --owner alice --folder-id private --user bob --role member >"$WORK_DIR/knowledge-scope.json"
json_assert "$WORK_DIR/knowledge-scope.json" 'data["snapshot"]["mode"] == "snapshot" and data["snapshot"]["item_ids"] == ["item-1"]'
"$OFFICE" knowledge-tree --space-type shared_with_me --user bob --role member >"$WORK_DIR/knowledge-shared-tree.json"
json_assert "$WORK_DIR/knowledge-shared-tree.json" 'len(data["items"]) >= 1'
"$OFFICE" knowledge-folder-create --space-type project --project p1 --folder-id specs --title Specs --created-by user-a --role project_manager >"$WORK_DIR/project-knowledge-folder.json"
"$OFFICE" knowledge-item-add --space-type project --project p1 --folder-id specs --item-id spec-1 --title Spec --source-ref local://spec.md --created-by user-a --role project_manager >"$WORK_DIR/project-knowledge-item.json"
"$OFFICE" knowledge-access-check --space-type project --project p1 --resource-type item --resource-id spec-1 --user user-a --role project_manager >"$WORK_DIR/project-knowledge-access.json"
json_assert "$WORK_DIR/project-knowledge-access.json" 'data["decision"]["allowed"] is True'
grep -q knowledge_acl_access "$HOME_DIR/agent-system/logs/knowledge-access.jsonl" || fail "knowledge ACL access log missing"

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
