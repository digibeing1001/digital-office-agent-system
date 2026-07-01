# cross-model-verification — 跨模型交叉验证

## 用途
对关键产出用不同模型家族交叉验证，防止单模型偏差。执行用模型 A 生成，评审用模型 B（不同家族）评分，agreement 低于阈值时触发第三方模型仲裁或 human_gate。与 `verification-loops`（同模型多样本）互补，cross-model-verification 是跨模型交叉。

适用于:最终交付前的跨模型验证、integrity gate 触发后的独立验证、评分争议时的第三方仲裁、human gate 前的可信度提升。

## 触发条件
- research-integrity-gates 的 cross_model_verification 配置触发
- verification-loops 分歧超阈值
- 评分处于临界区间（pass_threshold ± 0.5）
- 用户要求"交叉验证""换个模型评一下"
- 最终交付前的质量门控

## 操作步骤

### 步骤 1:配置模型家族
```python
MODEL_FAMILIES = {
    "anthropic": ["claude-sonnet-4", "claude-opus-4"],
    "openai": ["gpt-4o", "gpt-4-turbo"],
    "google": ["gemini-2.0-flash", "gemini-1.5-pro"],
    "local": ["llama-3-70b", "qwen-2-72b"],
}

def get_decoupled_judge(generation_model: str) -> str:
    """获取与生成模型不同家族的 judge 模型"""
    gen_family = _identify_family(generation_model)
    for family, models in MODEL_FAMILIES.items():
        if family != gen_family:
            return models[0]  # 返回第一个可用模型
    return generation_model  # 降级：无其他家族可用
```

### 步骤 2:跨模型评分
```python
async def cross_model_scoring(artifact: dict, generation_model: str, 
                               judge_models: list = None) -> dict:
    """用多个不同家族的模型独立评分"""
    if judge_models is None:
        judge_models = [get_decoupled_judge(generation_model)]
    
    scores = []
    for model in judge_models:
        score = await score_artifact(
            artifact,
            model=model,
            rubric=load_rubric(artifact["type"]),
            # 关键：judge 不知道生成模型是谁（防锚定偏差）
        )
        scores.append({
            "model": model,
            "family": _identify_family(model),
            "score": score["score"],
            "verdict": score["verdict"],
            "reasoning": score["reasoning"],
        })
    return scores
```

### 步骤 3:一致性计算
```python
def compute_agreement(scores: list) -> dict:
    """计算跨模型评分一致性"""
    score_values = [s["score"] for s in scores]
    
    # 一致性 = 1 - (标准差 / 评分范围)
    score_range = max(score_values) - min(score_values)
    std = (sum((s - sum(score_values)/len(score_values))**2 for s in score_values) / len(score_values)) ** 0.5
    agreement = 1 - (std / 7) if 7 > 0 else 1  # 7 是评分量表最大值
    
    # verdict 一致性
    verdicts = [s["verdict"] for s in scores]
    verdict_agreement = max(verdicts.count(v) for v in set(verdicts)) / len(verdicts)
    
    return {
        "score_agreement": round(agreement, 3),
        "verdict_agreement": round(verdict_agreement, 3),
        "score_std": round(std, 3),
        "score_range": score_range,
        "families_represented": list(set(s["family"] for s in scores)),
        "threshold_met": agreement >= 0.8,
    }
```

### 步骤 4:分歧处理
```python
def handle_disagreement(scores: list, agreement: dict) -> str:
    """处理跨模型分歧"""
    if agreement["threshold_met"]:
        return "complete"  # 一致性达标，可交付
    
    # 分歧超阈值，触发第三方仲裁
    if len(scores) < 3:
        return "escalate_arbitration"  # 需要第三方模型
    
    # 已有 3 个模型，取中位数
    score_values = sorted([s["score"] for s in scores])
    median = score_values[len(score_values) // 2]
    
    if median >= 6:  # pass_threshold
        return "complete_with_caveat"  # 中位数通过但带注意事项
    else:
        return "wait_human"  # 中位数不通过，需人工裁决
```

### 步骤 5:第三方仲裁
```python
async def third_party_arbitration(artifact: dict, scores: list) -> dict:
    """第三方模型仲裁"""
    # 选择第三个家族的模型
    used_families = set(s["family"] for s in scores)
    arbiter_model = None
    for family, models in MODEL_FAMILIES.items():
        if family not in used_families:
            arbiter_model = models[0]
            break
    
    if arbiter_model is None:
        return {"action": "wait_human", "reason": "no_third_family_available"}
    
    # 仲裁评分（告知前两个模型的分歧）
    arbiter_score = await score_artifact(
        artifact,
        model=arbiter_model,
        rubric=load_rubric(artifact["type"]),
        context=f"两个模型评分分歧: {scores}",  # 提供分歧上下文
    )
    
    return {
        "arbiter_model": arbiter_model,
        "arbiter_score": arbiter_score,
        "final_verdict": arbiter_score["verdict"],
        "action": "complete" if arbiter_score["verdict"] == "pass" else "replan",
    }
```

## 输出格式
```json
{
  "verification_type": "cross_model",
  "generation_model": "claude-sonnet-4",
  "judge_models": [
    {"model": "gpt-4o", "family": "openai", "score": 6, "verdict": "pass"},
    {"model": "gemini-2.0-flash", "family": "google", "score": 5, "verdict": "fail"}
  ],
  "agreement": {
    "score_agreement": 0.714,
    "verdict_agreement": 0.5,
    "threshold_met": false
  },
  "action": "escalate_arbitration",
  "arbiter": {
    "model": "llama-3-70b",
    "score": 6,
    "verdict": "pass",
    "final_action": "complete_with_caveat"
  }
}
```

## 约束
- judge 模型必须与生成模型不同家族（防家族内偏差）
- judge 不得知道生成模型身份（防锚定偏差）
- 一致性阈值 0.8（与 research-integrity-gates 对齐）
- 仲裁最多 1 轮（第三方模型），不得无限仲裁
- 仲裁仍分歧 → human_gate
- 跨模型验证成本较高，仅用于 final_delivery 和 integrity gate 触发时

## 与现有 skill 的关系
- **与 verification-loops 互补**:verification-loops 是同模型多样本，cross-model-verification 是跨模型交叉
- **与 research-integrity-gates 协同**:cross_model_verification 配置的数据源
- **与 cost-control.policy.json 协同**:跨模型验证成本纳入预算，仅 critical 场景触发
- **与 observability.policy.json 协同**:验证结果记录到 trace

## 依赖工具/API
- 多模型 API（Anthropic / OpenAI / Google / 本地模型）
- model-providers.registry.json（模型配置）

## 关键方法论引用
- academic-research-skills cross-model verification: https://github.com/Imbad0202/academic-research-skills
- research-integrity-gates.policy.json: cross_model_verification 配置
- GAN 式生成器-评估器对抗验证: gan-style-harness skill
