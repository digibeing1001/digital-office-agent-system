# research-scoring — 科研评分卡

## 用途
对 Agent 产出按六维评分(严谨性 / 新颖性 / 清晰度 / 可行性 / 影响力 / 置信度),混合 LLM 打分与外部工具核查(CRITIC 范式),避免纯 LLM 自评幻觉。合格线 75 分,任一可一票否决维度低于 50% 直接返工。

## 触发条件
- 每次 Agent 产出提交给下一角色前。
- 秘书(office-research-secretary)验收交付物时。
- 用户明确要求"评分""打分""验收"时。

## 工具依赖
无额外依赖,评分卡配置在 `profiles/office-research-secretary/scoring_config.yaml`:
```bash
pip install pyyaml  # 加载评分卡配置
```
工具核查(引用核查 / 可复现性 / 统计显著性 / 文献比对)调用对应 skill,不在此 skill 内实现。

## 操作步骤
1. 加载 `scoring_config.yaml`,读取六维权重、合格线、否决阈值。
2. 对每个维度打分(0-100),附理由(引用配置中的 description 作为评分依据)。
3. 对配置中标 `tool_checks` 的维度执行工具核查:
   - `citation_verification`:引用真实性核查(查 DOI/链接有效性)。
   - `reproducibility_check`:可复现性核查(代码/数据/随机种子是否齐备)。
   - `statistical_significance`:统计显著性(p 值/置信区间/效应量)。
   - `literature_comparison`:与近 2 年相关工作比对是否撞车。
   - `resource_assessment`:资源/时间/数据可得性评估。
4. 按权重算加权总分。
5. 检查一票否决:任一 `veto_eligible: true` 的维度得分 < `veto_threshold_percent`%(默认 50%),即使总分过线也判不通过。
6. 输出评分报告 JSON。

## 调用示例
```python
import yaml, json

def score_artifact(artifact, tool_check_results):
    with open("profiles/office-research-secretary/scoring_config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)["scoring"]

    scores, reasons = {}, {}
    for dim in cfg["dimensions"]:
        did = dim["id"]
        scores[did] = llm_score(artifact, dim)          # 0-100, 附理由
        reasons[did] = llm_reason(artifact, dim)
        # 对标 tool_checks 的维度做工具核查
        for chk in dim.get("tool_checks", []):
            if not tool_check_results.get(chk, False):
                scores[did] = min(scores[did], 49)      # 工具核查不过强制压分

    total = sum(scores[d["id"]] * d["weight"] for d in cfg["dimensions"]) / 100
    veto_pct = cfg["veto_threshold_percent"]
    veto_triggered = any(
        scores[d["id"]] < veto_pct for d in cfg["dimensions"] if d["veto_eligible"]
    )
    passed = (total >= cfg["pass_threshold"]) and not veto_triggered

    return {
        "scores": {k: {"score": v, "reason": reasons[k]} for k, v in scores.items()},
        "total": round(total, 2),
        "pass": passed,
        "veto_triggered": veto_triggered,
        "reasons": reasons,
    }
```

## 输出格式
评分报告 JSON:
```json
{
  "scores": {
    "soundness": {"score": 82, "reason": "方法正确,统计显著(p<0.01)"},
    "novelty":   {"score": 40, "reason": "与已有文献高度撞车"}
  },
  "total": 68.5,
  "pass": false,
  "veto_triggered": true,
  "reasons": {"soundness": "...", "novelty": "撞车,触发一票否决"}
}
```

## 约束
- 工具核查不可跳过:配置中标了 `tool_checks` 的维度必须执行对应核查,核查不过的维度强制压到否决线以下。
- 一票否决无条件触发返工,即使总分过 75 也判不通过。
- 置信度维度(confidence)是评分者对自身评分的自评,不参与工具核查,不触发否决。
- 评分必须附理由,不允许只给分不解释。
