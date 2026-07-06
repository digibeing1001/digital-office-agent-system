# self-reflection — 错误反思式反思环

## 用途
返工时生成反思文本,带着反思重写产出。返工不是简单重跑,而是先总结"哪里不够、为什么、下次怎么改",再把反思拼进 prompt 重写。

## 触发条件
- 评分卡(research-scoring)判定不通过时(总分 < 75 或一票否决触发)。
- 用户明确指出产出有问题需要返工时。

## 工具依赖
无额外依赖,反思文本存入 LangGraph checkpointer(单会话记忆):
```bash
pip install langgraph  # checkpointer 提供 single-session 反思记忆
```

## 操作步骤
1. 接收评分报告(哪些维度不够、为什么、是否一票否决)。
2. 生成反思文本,模板:"本次产出在 X 维度不够,原因是 Y,下次应该 Z"。
3. 把反思存入 checkpointer(单会话,key 用维度 id + 轮次)。
4. 把反思文本拼进 Agent 的 prompt,带反思重写产出。
5. 重写后重新调用 research-scoring 评分。
6. 若同一维度连续返工 >= 2 次,升级为 anti-pattern 写入经验库(跨会话),交由 experience-extraction 处理。
7. 最多返工 3 轮,超 3 轮上报用户决策。

## 调用示例
```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()

REFLECTION_PROMPT = """你是反思器。下面是上一轮产出和评分报告。
请生成反思文本,格式:"本次产出在 <维度> 维度不够,原因是 <具体原因>,下次应该 <可执行改进>"。

评分报告:
{score_report}

上一轮产出:
{artifact}

反思:"""

REWRITE_PROMPT = """请重写产出。你必须参考下面的反思,避免重蹈覆辙。

反思:
{reflection}

原始产出:
{artifact}

重写后的产出:"""

def reflect_and_rewrite(artifact, score_report, agent_id, thread_id):
    # 1. 生成反思
    reflection = llm_call(REFLECTION_PROMPT.format(
        score_report=json.dumps(score_report, ensure_ascii=False),
        artifact=artifact))

    # 2. 存入 checkpointer(单会话)
    dim = score_report.get("veto_dim", "overall")
    checkpointer.put(
        thread_id, f"reflection_{agent_id}_{dim}",
        {"reflection": reflection, "round": score_report.get("round", 1)})

    # 3. 带反思重写
    rewritten = llm_call(REWRITE_PROMPT.format(reflection=reflection, artifact=artifact))

    # 4. 重新评分
    new_score = score_artifact(rewritten, run_tool_checks(rewritten))

    # 5. 同一维度连续返工 >= 2 次,升级为 anti-pattern
    # 找触发否决的维度(低于50%的veto_eligible维度)
    new_veto_dims = [d for d, info in new_score.get("scores", {}).items()
                     if info.get("veto_eligible") and info.get("score", 100) < 50]
    new_dim = new_veto_dims[0] if new_veto_dims else "overall"
    if new_dim == dim and score_report.get("round", 1) >= 2:
        escalate_to_experience(agent_id, dim, reflection)  # 交 experience-extraction

    return {"reflection": reflection, "rewritten": rewritten, "new_score": new_score}
```

## 输出格式
```json
{
  "reflection": "本次产出在 novelty 维度不够,原因是与已有文献高度撞车,下次应该先查近 2 年 survey 再定方向",
  "rewritten": "<重写后的产出全文>",
  "new_score": {"total": 78.0, "pass": true, "veto_triggered": false}
}
```

## 约束
- 返工不是简单重跑,必须先生成反思再重写;不允许跳过反思直接重跑。
- 最多返工 3 轮,超 3 轮停止并上报用户决策,不让 Agent 无限循环。
- 反思文本必须可执行("下次应该 Z"要具体),不允许空话(如"下次注意")。
- 同一维度连续返工 >= 2 次必须升级为 anti-pattern 写入经验库,不能只停在单会话。
- 单会话反思存 checkpointer,不污染 SOUL.md 和跨会话经验库。
