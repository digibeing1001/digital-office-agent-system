# verification-loops — 多样本投票验证循环

## 用途
对关键产出执行多样本投票验证（pass@k metrics），通过多次独立采样 + 评分 + 多数表决，降低单次采样的随机性偏差。与 `quality-scoring.policy.json` 的 final_delivery 去偏配置和 `observability.policy.json` 的 eval_hooks 协同，是 ECC Verification Loops 理念的实现。

适用于:最终交付前的质量门控、integrity gate 触发后的交叉验证、评分处于临界线时的复验、human gate 前的可信度提升。

## 触发条件
- controller 准备发出 complete 决策前的 final_delivery 验证
- research-integrity-gates 触发后的二次验证
- 评分处于 pass_threshold ± 1 的临界区间
- 用户要求"复验""交叉检查""再跑一遍"
- cost-control 告警 critical 时的产出可信度确认

## 操作步骤

### 步骤 1:配置验证参数
```python
VERIFICATION_CONFIG = {
    "samples": 3,              # 采样次数（与 quality-scoring final_delivery 一致）
    "temperature": 0.7,        # 采样温度（与 quality-scoring 一致）
    "voting_mode": "majority", # 多数表决
    "disagreement_threshold": 1.0,  # 分歧阈值（与 quality-scoring 一致）
    "min_pass_count": 2,       # 至少 N 次通过才算通过
    "judge_decoupled": True,   # 评分用不同模型（防自评偏差）
}
```

### 步骤 2:多样本采样
```python
async def multi_sample_generation(artifact_spec: dict, samples: int = 3) -> list:
    """对同一产出规格独立采样 N 次"""
    import asyncio
    tasks = []
    for i in range(samples):
        # 每次采样用独立随机种子 + 高温
        task = generate_artifact(artifact_spec, seed=i*1000, temperature=0.7)
        tasks.append(task)
    return await asyncio.gather(*tasks)
```

### 步骤 3:独立评分
```python
async def independent_scoring(artifacts: list, judge_model: str = None) -> list:
    """用解耦的 judge 模型对每个样本独立评分"""
    scores = []
    for artifact in artifacts:
        # judge_model 与生成模型不同家族（防自评偏差）
        score = await score_artifact(
            artifact,
            model=judge_model or get_decoupled_judge(),
            rubric=load_rubric(artifact["type"]),
        )
        scores.append(score)
    return scores
```

### 步骤 4:投票与分歧检测
```python
def vote_and_detect_disagreement(scores: list, threshold: float = 1.0) -> dict:
    """多数表决 + 分歧检测"""
    verdicts = [s["verdict"] for s in scores]
    pass_count = verdicts.count("pass")
    fail_count = verdicts.count("fail")
    
    # 分歧度 = 最高分 - 最低分
    score_values = [s["score"] for s in scores]
    disagreement = max(score_values) - min(score_values)
    
    # 多数表决
    majority_verdict = "pass" if pass_count > fail_count else "fail"
    
    return {
        "majority_verdict": majority_verdict,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "disagreement": disagreement,
        "disagreement_exceeded": disagreement > threshold,
        "scores": scores,
        "needs_human_gate": disagreement > threshold or pass_count == fail_count,
    }
```

### 步骤 5:验证循环决策
```python
def verification_loop_decision(vote_result: dict) -> str:
    """根据投票结果决定下一步"""
    if vote_result["majority_verdict"] == "pass" and not vote_result["disagreement_exceeded"]:
        return "complete"  # 通过验证，可交付
    elif vote_result["needs_human_gate"]:
        return "wait_human"  # 分歧过大，需人工裁决
    elif vote_result["majority_verdict"] == "fail":
        return "replan"  # 多数失败，需返工
    else:
        return "retry"  # 边界情况，重试验证
```

### 步骤 6:记录验证轨迹
```python
def record_verification_trace(run_id: str, vote_result: dict):
    """记录到 scoring_trajectory 和 observability trace"""
    # 写入评分轨迹
    traj_entry = {
        "cycle": get_current_cycle(run_id),
        "node": "evaluate",
        "verification_type": "multi_sample_voting",
        "samples": vote_result["pass_count"] + vote_result["fail_count"],
        "majority_verdict": vote_result["majority_verdict"],
        "disagreement": vote_result["disagreement"],
        "scores": vote_result["scores"],
        "timestamp": now_iso(),
    }
    append_to(f"agent-system/runs/{run_id}/scoring_trajectory.jsonl", traj_entry)
```

## 输出格式
```json
{
  "verification_type": "multi_sample_voting",
  "samples_generated": 3,
  "majority_verdict": "pass",
  "pass_count": 2,
  "fail_count": 1,
  "disagreement": 0.5,
  "disagreement_exceeded": false,
  "decision": "complete",
  "scores": [
    {"sample_id": 0, "score": 6, "verdict": "pass"},
    {"sample_id": 1, "score": 5.5, "verdict": "pass"},
    {"sample_id": 2, "score": 5.0, "verdict": "fail"}
  ]
}
```

## 约束
- 采样必须独立（不同随机种子，不得共享上下文）
- judge 模型必须与生成模型解耦（不同家族，防自评偏差）
- 分歧超阈值时必须走 human_gate，不得自动放行
- pass_count == fail_count 时必须走 human_gate
- 验证循环最多 2 轮（防止成本失控，与 cost-control max_rework_cycles 对齐）
- 每次验证记录到 scoring_trajectory（与 research-integrity-gates 协同）

## 与现有 skill 的关系
- **与 quality-scoring.policy.json 协同**:verification-loops 是 final_delivery 去偏的实现层
- **与 observability.policy.json 协同**:验证结果记录到 eval_hooks
- **与 cross-model-verification 协同**:verification-loops 是同模型多样本，cross-model-verification 是跨模型交叉
- **与 research-integrity-gates 协同**:integrity gate 触发时自动触发 verification-loops

## 依赖工具/API
- LLM API（多样本生成）
- 解耦 judge 模型（不同家族）
- scoring_trajectory 存储

## 关键方法论引用
- ECC Verification Loops: https://github.com/affaan-m/ECC
- pass@k metrics: HumanEval (Chen et al., 2021)
- quality-scoring.policy.json: agent-system/quality-scoring.policy.json (final_delivery 去偏配置)
