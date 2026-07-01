# reflexion-loop — 4 策略反思循环

## 用途
基于 Reflexion 论文（Shinn et al., NeurIPS 2023）的 4 种反思策略，在任务失败或评分不达标时，Agent 进行口头反思并将反思文本存入情景记忆缓冲区，供后续尝试使用。不更新模型权重，纯 prompt 层面进化。与 `experience-extraction`（项目级经验）互补，reflexion-loop 是任务级实时反思。

适用于:单次任务失败后的即时反思改进、评分不达标时的自我修正、实验失败的根因分析、写作返工的策略调整。

## 触发条件
- Act 节点动作失败
- Evaluate 节点评分低于 pass_threshold
- research-integrity-gates 触发 replan
- controller 发出 retry 决策
- 用户要求"反思一下""想想为什么失败"

## 操作步骤

### 步骤 1:选择反思策略
```python
REFLEXION_STRATEGIES = {
    "NONE": "不反思，直接重试（基线策略）",
    "LAST_ATTEMPT": "仅参考上一次尝试的输出，不做显式反思",
    "REFLEXION": "仅参考反思文本，不参考上一次输出",
    "LAST_ATTEMPT_AND_REFLEXION": "同时参考上一次输出和反思文本（推荐）",
}

def select_strategy(failure_class: str, attempt_count: int) -> str:
    """根据失败类型和尝试次数选择策略"""
    if attempt_count == 1:
        return "LAST_ATTEMPT"  # 第一次失败，简单参考
    elif attempt_count >= 3:
        return "NONE"  # 超过 3 次，反思无效，升级 human_gate
    else:
        return "LAST_ATTEMPT_AND_REFLEXION"  # 推荐策略
```

### 步骤 2:生成反思
```python
def generate_reflection(failed_attempt: dict, failure_feedback: dict, 
                        strategy: str = "LAST_ATTEMPT_AND_REFLEXION") -> str:
    """LLM 生成口头反思文本"""
    prompt = f"""
    你刚才的任务失败了，请反思原因并制定改进策略。
    
    失败的任务输出:
    {failed_attempt.get('output', '')}
    
    失败反馈:
    - 失败类型: {failure_feedback.get('failure_class', 'unknown')}
    - 评分: {failure_feedback.get('score', 'N/A')}
    - 具体问题: {failure_feedback.get('issues', [])}
    
    请回答:
    1. 为什么失败了？（根因分析）
    2. 具体哪里出了问题？（定位）
    3. 下次应该怎么做？（可执行改进）
    4. 要避免什么？（anti-pattern）
    
    反思要具体、可执行，不要空话。
    """
    reflection = llm_call(prompt)
    
    # 存入情景记忆缓冲区
    save_to_episodic_memory(
        agent_id=failed_attempt["agent_id"],
        task_id=failed_attempt["task_id"],
        reflection=reflection,
        strategy=strategy,
    )
    return reflection
```

### 步骤 3:检索相关反思
```python
def retrieve_reflections(agent_id: str, task_context: str, top_k: int = 3) -> list:
    """从情景记忆缓冲区检索相关反思"""
    reflections = load_episodic_memory(agent_id)
    
    # 按任务相似度排序
    scored = []
    for r in reflections:
        sim = compute_similarity(task_context, r["task_context"])
        scored.append((sim, r))
    
    scored.sort(key=lambda x: -x[0])
    return [r for _, r in scored[:top_k]]
```

### 步骤 4:带反思的重试
```python
def retry_with_reflection(task_spec: dict, agent_id: str, strategy: str) -> dict:
    """带反思的重试"""
    reflections = retrieve_reflections(agent_id, task_spec["context"])
    
    # 根据策略构建 prompt
    if strategy == "NONE":
        prompt = task_spec["prompt"]
    elif strategy == "LAST_ATTEMPT":
        prompt = f"{task_spec['prompt']}\n\n上次输出（参考）:\n{get_last_output(agent_id, task_spec['task_id'])}"
    elif strategy == "REFLEXION":
        prompt = f"{task_spec['prompt']}\n\n反思记录（参考）:\n" + \
                 "\n".join([f"- {r['reflection']}" for r in reflections])
    else:  # LAST_ATTEMPT_AND_REFLEXION
        prompt = f"{task_spec['prompt']}\n\n上次输出:\n{get_last_output(agent_id, task_spec['task_id'])}\n\n反思记录:\n" + \
                 "\n".join([f"- {r['reflection']}" for r in reflections])
    
    return generate_with_prompt(prompt, task_spec.get("model"))
```

### 步骤 5:反思质量评估
```python
def evaluate_reflection_quality(reflection: str, subsequent_result: dict) -> dict:
    """评估反思是否有效（后续尝试是否改善）"""
    return {
        "reflection": reflection[:200],
        "subsequent_score": subsequent_result.get("score"),
        "subsequent_verdict": subsequent_result.get("verdict"),
        "improved": subsequent_result.get("score", 0) > get_previous_score(subsequent_result["agent_id"]),
        "reflection_effective": subsequent_result.get("verdict") == "pass",
    }
```

## 输出格式
```json
{
  "agent_id": "academic-writer",
  "task_id": "draft-introduction",
  "attempt": 2,
  "strategy": "LAST_ATTEMPT_AND_REFLEXION",
  "reflection": "上次失败原因：引言缺乏问题动机的明确阐述。改进策略：先用1段描述现有方法的局限性，再引出我们的方法...",
  "reflections_retrieved": 2,
  "subsequent_result": {"score": 6.5, "verdict": "pass"},
  "improved": true,
  "reflection_effective": true
}
```

## 约束
- 反思必须具体可执行，不允许空话（如"注意质量"）
- 反思存入情景记忆缓冲区，跨会话有效（与 cross-run-memory 协同）
- 最多 3 次反思循环（与 cost-control max_rework_cycles 对齐）
- 超过 3 次仍失败 → 升级 human_gate + 写入 experience-extraction 作为项目级教训
- 无效反思（后续未改善）降权，有效反思升权
- 反思文本最大 500 字（防止 prompt 膨胀）

## 与现有 skill 的关系
- **与 experience-extraction 互补**:reflexion-loop 是任务级实时反思，experience-extraction 是项目级经验沉淀
- **与 failure-mode-archiving 协同**:reflexion-loop 生成反思，failure-mode-archiving 归档失败模式
- **与 cross-run-memory 协同**:反思存入 cross-run-memory 实现跨会话复用
- **与 research-integrity-gates 协同**:integrity gate 触发时自动触发 reflexion-loop

## 依赖工具/API
- LLM API（反思生成）
- 情景记忆缓冲区（文件存储）

## 关键方法论引用
- Reflexion: Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning", NeurIPS 2023
- 4 策略: NONE / LAST_ATTEMPT / REFLEXION / LAST_ATTEMPT_AND_REFLEXION
- arXiv: https://arxiv.org/abs/2303.11366
