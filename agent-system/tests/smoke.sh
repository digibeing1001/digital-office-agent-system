#!/usr/bin/env bash
# research-team smoke test skeleton
# Adapted from main branch agent-system/tests/smoke.sh v2.0.0 for research-team
# (cross-learning 2026-07). Focuses on research-integrity gates, context-envelope
# v2.0.1-research specialization, and skills.sources candidate inventory.
#
# json_assert runs a Python expression over the parsed JSON `data` object.
# must_fail inverts a command's exit code (expects non-zero).
set -euo pipefail

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

# must_fail: run a command and assert it exits non-zero.
# Usage: must_fail <command...>
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

# json_assert: parse a JSON file and evaluate a Python expression over `data`.
# Usage: json_assert <file> <expr> <description>
#   file        : relative path to JSON file
#   expr        : Python expression; `data` holds the parsed JSON object
#   description : human-readable test description (printed on pass)
json_assert() {
  local file="$1"
  local expr="$2"
  local desc="$3"
  python3 - "$file" "$expr" "$desc" <<'PY'
import json
import sys

path, expr, desc = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, "r", encoding="utf-8") as handle:
    data = json.load(handle)
if not eval(expr, {"__builtins__": {"all": all, "any": any, "len": len, "list": list, "set": set}}, {"data": data}):
    raise SystemExit(f"assertion failed: {desc}\n  expr: {expr}\n  file: {path}\n{json.dumps(data, ensure_ascii=False, indent=2)}")
print(f"  ok  {desc}")
PY
}

cd "$SOURCE_ROOT"

# ---------------------------------------------------------------------------
# JSON validity sweep: every tracked .json must parse.
# ---------------------------------------------------------------------------
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  json_files="$(git ls-files "*.json")"
else
  json_files="$(find agent-system -type f -name "*.json" | sort)"
fi
for file in $json_files; do
  python3 -m json.tool "$file" >/dev/null
done
echo "  ok  all tracked JSON files parse"
python3 agent-system/tests/feishu-team-smoke.py

# ---------------------------------------------------------------------------
# Test 1: context-envelope schema version is research-specialized
# ---------------------------------------------------------------------------
json_assert agent-system/context-envelope.schema.json \
  'data["properties"]["version"]["const"] == "2.0.1-research"' \
  "context-envelope schema version is 2.0.1-research"

# ---------------------------------------------------------------------------
# Test 2: context-envelope schema has research_specific block
# ---------------------------------------------------------------------------
json_assert agent-system/context-envelope.schema.json \
  '"research_specific" in data["properties"] and {"literature_refs","hypothesis_lock","experiment_log_ref"} <= set(data["properties"]["research_specific"]["properties"])' \
  "context-envelope schema has research_specific fields (literature_refs, hypothesis_lock, experiment_log_ref)"

# ---------------------------------------------------------------------------
# Test 3: research-integrity-gates defines exactly 7 gate modes
# ---------------------------------------------------------------------------
json_assert agent-system/research-integrity-gates.policy.json \
  'len(data["gate_modes"]) == 7' \
  "research-integrity-gates defines 7 gate modes"

# ---------------------------------------------------------------------------
# Test 4: every gate mode has required_outputs and pass_conditions
# ---------------------------------------------------------------------------
json_assert agent-system/research-integrity-gates.policy.json \
  'all("required_outputs" in g and "pass_conditions" in g for g in data["gate_modes"])' \
  "every integrity gate has required_outputs and pass_conditions"

# ---------------------------------------------------------------------------
# Test 5: data_fabrication gate is non-negotiable (max_rework == 0)
# ---------------------------------------------------------------------------
json_assert agent-system/research-integrity-gates.policy.json \
  'any(g["id"] == "data_fabrication" and g["max_rework"] == 0 for g in data["gate_modes"])' \
  "data_fabrication gate has max_rework=0 (non-negotiable)"

# ---------------------------------------------------------------------------
# Test 6: coordination.policy has enhancement_version field (2026-07 iteration)
# ---------------------------------------------------------------------------
json_assert agent-system/coordination.policy.json \
  'data.get("enhancement_version") == "2026-07-01"' \
  "coordination.policy has enhancement_version 2026-07-01"

# ---------------------------------------------------------------------------
# Test 7: coordination.policy exposes parallel_expert_dag and human_gated modes
# ---------------------------------------------------------------------------
json_assert agent-system/coordination.policy.json \
  '"parallel_expert_dag" in data["modes"] and "human_gated" in data["modes"]' \
  "coordination.policy has parallel_expert_dag and human_gated modes"

# ---------------------------------------------------------------------------
# Test 8: skills.sources has >= 9 candidate_sources
# ---------------------------------------------------------------------------
json_assert agent-system/skills.sources.json \
  'len(data.get("candidate_sources", [])) >= 9' \
  "skills.sources has at least 9 candidate_sources"

# ---------------------------------------------------------------------------
# Test 9: research-integrity-gates has scoring_trajectory_tracking
# ---------------------------------------------------------------------------
json_assert agent-system/research-integrity-gates.policy.json \
  '"scoring_trajectory_tracking" in data and "fields" in data["scoring_trajectory_tracking"]' \
  "research-integrity-gates has scoring_trajectory_tracking with fields"

# ---------------------------------------------------------------------------
# Test 10: research-integrity-gates has cross_model_verification
# ---------------------------------------------------------------------------
json_assert agent-system/research-integrity-gates.policy.json \
  '"cross_model_verification" in data and data["cross_model_verification"]["strategy"]["min_models"] >= 2' \
  "research-integrity-gates has cross_model_verification requiring >= 2 models"

# ---------------------------------------------------------------------------
# Test 11: hallucinated_citation gate requires citation_verification_report
# ---------------------------------------------------------------------------
json_assert agent-system/research-integrity-gates.policy.json \
  'any(g["id"] == "hallucinated_citation" and "citation_verification_report" in g["required_outputs"] for g in data["gate_modes"])' \
  "hallucinated_citation gate requires citation_verification_report output"

# ---------------------------------------------------------------------------
# Test 12: reproducibility_gap gate requires reproducibility_checklist
# ---------------------------------------------------------------------------
json_assert agent-system/research-integrity-gates.policy.json \
  'any(g["id"] == "reproducibility_gap" and "reproducibility_checklist" in g["required_outputs"] for g in data["gate_modes"])' \
  "reproducibility_gap gate requires reproducibility_checklist output"

# ---------------------------------------------------------------------------
# must_fail: json_assert with a false expression must exit non-zero
# ---------------------------------------------------------------------------
must_fail json_assert agent-system/coordination.policy.json \
  'data.get("enhancement_version") == "WRONG-VERSION"' \
  "must_fail guard: wrong enhancement_version should not pass"

# ---------------------------------------------------------------------------
# must_fail: json.tool on a non-JSON file must exit non-zero
# ---------------------------------------------------------------------------
printf 'not-json{' > "$WORK_DIR/bad.json"
must_fail python3 -m json.tool "$WORK_DIR/bad.json"

echo "smoke-ok"
# End of research-team smoke.sh skeleton.
# Absorption note: this skeleton adapts main's json_assert + must_fail pattern
# for research-team-specific assertions (integrity gates, context-envelope
# v2.0.1-research, skills.sources inventory). Integration tests that require
# the full office-system runtime (workflow-start, agent-invoke, knowledge-*)
# are intentionally omitted from the skeleton; add them when the research-team
# runtime harness is wired up.
