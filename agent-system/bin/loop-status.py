#!/usr/bin/env python3
"""
loop-status.py — 数字办公室 Loop 状态查询命令

参考 ECC 的 `ecc status` 命令设计，提供单命令查看：
- run readiness（是否就绪继续）
- active sessions（当前活跃的 loop run）
- score trend（评分趋势）
- cost so far + budget remaining（已花费 + 剩余预算）
- integrity gate status（完整性门控状态）
- pending human gates（待人工审批）

用法：
  python loop-status.py [--run-id <run_id>] [--markdown] [--exit-code]

--markdown: 输出 markdown 格式，适合写入 status.md
--exit-code: readiness 不达标时返回非零退出码，用于 CI 门控

依赖文件：
  agent-system/runs/<run_id>/run.json
  agent-system/runs/<run_id>/ledger.jsonl
  agent-system/runs/<run_id>/costs.jsonl
  agent-system/runs/<run_id>/scoring_trajectory.jsonl
  agent-system/runs/<run_id>/traces.jsonl
"""
import argparse
import json
import os
import sys
from pathlib import Path

AGENT_SYSTEM = Path(__file__).resolve().parent.parent
RUNS_DIR = AGENT_SYSTEM / "runs"


def load_run(run_id: str) -> dict:
    run_file = RUNS_DIR / run_id / "run.json"
    if not run_file.exists():
        return {"error": f"run not found: {run_id}"}
    return json.loads(run_file.read_text(encoding="utf-8"))


def load_costs(run_id: str) -> list:
    costs_file = RUNS_DIR / run_id / "costs.jsonl"
    if not costs_file.exists():
        return []
    return [json.loads(line) for line in costs_file.read_text(encoding="utf-8").strip().split("\n") if line]


def load_scoring_trajectory(run_id: str) -> list:
    traj_file = RUNS_DIR / run_id / "scoring_trajectory.jsonl"
    if not traj_file.exists():
        return []
    return [json.loads(line) for line in traj_file.read_text(encoding="utf-8").strip().split("\n") if line]


def load_integrity_gates(run_id: str) -> list:
    """从 trace 中提取 integrity gate 事件"""
    trace_file = RUNS_DIR / run_id / "traces.jsonl"
    if not trace_file.exists():
        return []
    gates = []
    for line in trace_file.read_text(encoding="utf-8").strip().split("\n"):
        if not line:
            continue
        span = json.loads(line)
        if span.get("type") == "integrity_gate":
            gates.append(span)
    return gates


def compute_cost_summary(costs: list, budget_microunits: int) -> dict:
    total = sum(c.get("cost_microunits", 0) for c in costs)
    return {
        "total_cost_microunits": total,
        "budget_microunits": budget_microunits,
        "remaining_microunits": budget_microunits - total,
        "utilization_pct": round(total / budget_microunits * 100, 1) if budget_microunits > 0 else 0,
        "by_agent": _group_by(costs, "agent_id", "cost_microunits"),
        "by_model": _group_by(costs, "model", "cost_microunits"),
    }


def _group_by(items: list, key: str, sum_key: str) -> dict:
    result = {}
    for item in items:
        k = item.get(key, "unknown")
        result[k] = result.get(k, 0) + item.get(sum_key, 0)
    return result


def compute_score_trend(trajectory: list) -> dict:
    if not trajectory:
        return {"trend": "no_data", "volatility": 0, "last_score": None}
    scores = [t["score"] for t in trajectory if "score" in t]
    if len(scores) < 2:
        return {"trend": "insufficient_data", "volatility": 0, "last_score": scores[-1] if scores else None}
    # 简单线性回归斜率
    n = len(scores)
    x_mean = (n - 1) / 2
    y_mean = sum(scores) / n
    numerator = sum((i - x_mean) * (s - y_mean) for i, s in enumerate(scores))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    slope = numerator / denominator if denominator != 0 else 0
    # 最近 3 次标准差
    recent = scores[-3:]
    recent_mean = sum(recent) / len(recent)
    volatility = (sum((s - recent_mean) ** 2 for s in recent) / len(recent)) ** 0.5
    return {
        "trend": "improving" if slope > 0.1 else ("degrading" if slope < -0.1 else "stable"),
        "slope": round(slope, 3),
        "volatility": round(volatility, 3),
        "last_score": scores[-1],
        "cycle_count": n,
    }


def assess_readiness(run: dict, cost_summary: dict, score_trend: dict, gates: list) -> dict:
    """评估是否就绪继续"""
    issues = []
    status = run.get("status", "unknown")
    if status in ["failed", "cancelled", "budget_exhausted"]:
        issues.append(f"run is terminal: {status}")
    if cost_summary["utilization_pct"] >= 90:
        issues.append(f"budget nearly exhausted: {cost_summary['utilization_pct']}%")
    if score_trend["trend"] == "degrading":
        issues.append(f"score trend degrading: slope={score_trend['slope']}")
    failed_gates = [g for g in gates if g.get("gate_result") == "blocked"]
    if failed_gates:
        issues.append(f"{len(failed_gates)} integrity gates blocked")
    return {
        "ready": len(issues) == 0,
        "issues": issues,
    }


def render_plain(run_id: str, run: dict, cost_summary: dict, score_trend: dict, gates: list, readiness: dict) -> str:
    lines = [
        f"=== Loop Status: {run_id} ===",
        f"Status:          {run.get('status', 'unknown')}",
        f"Current Node:    {run.get('current_node', 'unknown')}",
        f"Controller:      {run.get('controller_decision', 'unknown')}",
        f"Cycles:          {run.get('cycle_count', 0)}",
        "",
        f"--- Cost ---",
        f"Total:           {cost_summary['total_cost_microunits']} micro-units",
        f"Budget:          {cost_summary['budget_microunits']} micro-units",
        f"Remaining:       {cost_summary['remaining_microunits']} micro-units ({100 - cost_summary['utilization_pct']}%)",
        f"Utilization:     {cost_summary['utilization_pct']}%",
        "",
        f"--- Score Trend ---",
        f"Trend:           {score_trend['trend']}",
        f"Last Score:      {score_trend['last_score']}",
        f"Volatility:      {score_trend['volatility']}",
        f"Cycles Scored:   {score_trend['cycle_count']}",
        "",
        f"--- Integrity Gates ---",
        f"Total Triggered: {len(gates)}",
        f"Blocked:         {len([g for g in gates if g.get('gate_result') == 'blocked'])}",
    ]
    if readiness["issues"]:
        lines.append("")
        lines.append("--- Readiness Issues ---")
        for issue in readiness["issues"]:
            lines.append(f"  ! {issue}")
    lines.append("")
    lines.append(f"Ready: {'YES' if readiness['ready'] else 'NO'}")
    return "\n".join(lines)


def render_markdown(run_id: str, run: dict, cost_summary: dict, score_trend: dict, gates: list, readiness: dict) -> str:
    lines = [
        f"# Loop Status: `{run_id}`",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| Status | {run.get('status', 'unknown')} |",
        f"| Current Node | {run.get('current_node', 'unknown')} |",
        f"| Controller Decision | {run.get('controller_decision', 'unknown')} |",
        f"| Cycles | {run.get('cycle_count', 0)} |",
        "",
        "## Cost",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Total Spent | {cost_summary['total_cost_microunits']} micro-units |",
        f"| Budget | {cost_summary['budget_microunits']} micro-units |",
        f"| Remaining | {cost_summary['remaining_microunits']} ({100 - cost_summary['utilization_pct']}%) |",
        f"| Utilization | {cost_summary['utilization_pct']}% |",
        "",
        "## Score Trend",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Trend | {score_trend['trend']} |",
        f"| Last Score | {score_trend['last_score']} |",
        f"| Volatility | {score_trend['volatility']} |",
        "",
        "## Integrity Gates",
        f"- Total Triggered: {len(gates)}",
        f"- Blocked: {len([g for g in gates if g.get('gate_result') == 'blocked'])}",
        "",
    ]
    if readiness["issues"]:
        lines.append("## Readiness Issues")
        for issue in readiness["issues"]:
            lines.append(f"- ! {issue}")
        lines.append("")
    lines.append(f"**Ready: {'YES' if readiness['ready'] else 'NO'}**")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Loop status query")
    parser.add_argument("--run-id", default=os.environ.get("LOOP_RUN_ID", ""), help="Run ID to query")
    parser.add_argument("--markdown", action="store_true", help="Output markdown format")
    parser.add_argument("--exit-code", action="store_true", help="Exit non-zero if not ready (for CI)")
    args = parser.parse_args()

    if not args.run_id:
        print("Error: --run-id required (or set LOOP_RUN_ID env)", file=sys.stderr)
        sys.exit(2)

    run = load_run(args.run_id)
    if "error" in run:
        print(run["error"], file=sys.stderr)
        sys.exit(2)

    costs = load_costs(args.run_id)
    trajectory = load_scoring_trajectory(args.run_id)
    gates = load_integrity_gates(args.run_id)

    budget = run.get("budget", {}).get("max_cost_microunits", 5000000)
    cost_summary = compute_cost_summary(costs, budget)
    score_trend = compute_score_trend(trajectory)
    readiness = assess_readiness(run, cost_summary, score_trend, gates)

    if args.markdown:
        print(render_markdown(args.run_id, run, cost_summary, score_trend, gates, readiness))
    else:
        print(render_plain(args.run_id, run, cost_summary, score_trend, gates, readiness))

    if args.exit_code and not readiness["ready"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
