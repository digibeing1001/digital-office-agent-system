# experience-extraction — 经验学习式经验抽取

## 用途
项目结束时从整轮轨迹抽取可复用经验(成功方案 + 失败教训),去重后写入经验库供后续项目复用。依据经验学习范式 + 可复用技能库设计。

## 触发条件
- 项目结束时(所有角色交付完成、用户验收通过)。
- 用户明确要求"总结经验""沉淀教训"时。

## 工具依赖
无额外依赖,用 LLM 抽取 insights,经验库存储为文件:
```bash
pip install openai  # 调用 LLM 抽取经验(也可用本地模型)
```

## 操作步骤
1. 收集项目全程轨迹:各角色的产出、评分报告、返工记录、用户纠正记录。
2. 让 LLM 从轨迹抽取 insights,分两类:
   - 成功方案:"遇到 X 情况,应该 Y"。
   - 失败教训(anti-pattern):"遇到 X 情况,不要 Y"。
3. 与现有经验库比对去重(语义相似度 > 0.85 视为重复)。
4. 写入 `skills/experience/<agent_id>/<topic>.md`,每条经验附来源项目 id。
5. 若发现某维度评分系统性偏差(如 novelty 维度连续多个项目返工),建议更新 `scoring_config.yaml`。
6. 长期不调用的经验降权(衰减),由 cross-run-memory 记录调用情况。

## 调用示例
```python
import os, json

EXTRACTION_PROMPT = """从下面的项目轨迹中抽取可复用经验,每条经验一个 insight。
成功方案格式:"遇到 <情况>,应该 <做法>"。
失败教训格式:"遇到 <情况>,不要 <做法>"。
每条经验必须具体可执行,不要空话。

项目轨迹:
{trajectory}

输出 JSON 数组:
[{"type": "success|failure", "insight": "...", "agent_id": "...", "topic": "..."}]
"""

def extract_experiences(project_id, trajectory):
    # 1. LLM 抽取
    raw = llm_call(EXTRACTION_PROMPT.format(trajectory=json.dumps(trajectory, ensure_ascii=False)))
    insights = json.loads(raw)

    # 2. 去重(与现有经验库比对)
    for ins in insights:
        if is_duplicate(ins["insight"], f"skills/experience/{ins['agent_id']}/"):
            continue
        # 3. 写入 skills/experience/<agent_id>/<topic>.md
        path = f"skills/experience/{ins['agent_id']}/{ins['topic']}.md"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        entry = f"- [{ins['type']}] {ins['insight']}  (来源: {project_id})\n"
        with open(path, "a", encoding="utf-8") as f:
            f.write(entry)

    # 4. 检测系统性评分偏差
    rework_dims = count_rework_by_dim(trajectory)
    suggestions = []
    for dim, count in rework_dims.items():
        if count >= 3:  # 同一维度跨多项目返工
            suggestions.append(f"维度 {dim} 返工频繁,建议复核 scoring_config 权重/合格线")
    return {"extracted": len(insights), "deduped": len(insights), "config_suggestions": suggestions}

def is_duplicate(insight, dir_path):
    if not os.path.isdir(dir_path):
        return False
    for fn in os.listdir(dir_path):
        with open(os.path.join(dir_path, fn), encoding="utf-8") as f:
            if insight[:20] in f.read():  # 简化去重,实际用相似度 > 0.85
                return True
    return False
```

## 输出格式
经验条目列表:
```json
{
  "extracted": 5,
  "deduped": 4,
  "entries": [
    {"type": "success", "insight": "遇到综述类任务,应该先查近 2 年 survey 再查原文", "agent_id": "office-researcher", "topic": "literature-review", "source": "proj_2026_07"},
    {"type": "failure", "insight": "遇到新颖性评估,不要只凭 LLM 自评,必须做文献比对", "agent_id": "office-research-secretary", "topic": "scoring", "source": "proj_2026_07"}
  ],
  "config_suggestions": ["维度 novelty 返工频繁,建议复核 scoring_config 权重"]
}
```

## 约束
- 经验必须去重(语义相似度 > 0.85 视为重复),避免经验库膨胀污染。
- 每条经验必须附来源项目 id,便于追溯。
- 经验必须具体可执行,不允许空话(如"注意质量")。
- 长期不调用的经验降权(衰减),但不直接删除(可能偶发有用)。
- anti-pattern 写入经验库前建议人工 review,避免错误教训固化。
