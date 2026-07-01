# preference-internalization — 用户纠正内化

## 用途
用户纠正某个 Agent 的做法时,判断是通用偏好(以后都这样)还是一次性指正(仅本次),分别内化到 SOUL.md 或 checkpointer。依据 Reflexion 反思 + mem0 偏好持久化。

## 触发条件
- 用户明确纠正某个 Agent 的做法(如"以后查文献不要只用 Google Scholar")。
- 用户对产出表达明确的偏好性反馈(如"报告里不要用第一人称")。

## 工具依赖
无额外依赖:
```bash
pip install pyyaml  # 读写 SOUL.md 配套的 config.yaml(可选)
```

## 操作步骤
1. 识别用户纠正内容(从对话中提取纠正句)。
2. 判断纠正类型:
   - 通用偏好:用户用"以后""总是""每次"等词,或表达长期规则。
   - 一次性指正:用户用"这次""仅本次""这个项目"等词,或针对具体场景。
3. 不确定时,反问用户:"这是通用偏好(以后都这样)还是本次指正?"
4. 通用偏好 → 写入该 Agent 的 `profiles/<agent_id>/SOUL.md`,格式:`[用户偏好 YYYY-MM-DD] 规则内容`。
5. 一次性指正 → 存入当前项目 checkpointer(thread_id 为项目 id),不污染长期记忆。
6. 通知用户已内化(告知内化目标和内容)。

## 调用示例
```python
import datetime, os

JUDGE_PROMPT = """判断下面用户纠正的类型:
- general: 通用偏好,用户希望以后都这样(含"以后""总是""每次"等)
- one_off: 一次性指正,仅针对本次/本项目(含"这次""仅本次""这个项目"等)
- uncertain: 无法判断

用户纠正:{correction}

输出 JSON: {{"type": "general|one_off|uncertain", "reason": "..."}}
"""

def internalize_preference(agent_id, correction, thread_id=None, user_confirmed=None):
    # 1. 判断类型(若用户已确认则跳过判断)
    if user_confirmed:
        ptype = user_confirmed
    else:
        result = llm_call(JUDGE_PROMPT.format(correction=correction))
        ptype = json.loads(result)["type"]
        if ptype == "uncertain":
            return {"need_clarification": True,
                    "question": "这是通用偏好(以后都这样)还是本次指正?"}

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    if ptype == "general":
        # 2. 通用偏好 → 写入 SOUL.md
        soul_path = f"profiles/{agent_id}/SOUL.md"
        entry = f"\n[用户偏好 {date_str}] {correction}\n"
        with open(soul_path, "a", encoding="utf-8") as f:
            f.write(entry)
        target = f"SOUL.md ({soul_path})"
    else:
        # 3. 一次性 → 存 checkpointer
        checkpointer.put(thread_id, f"pref_{agent_id}_{date_str}",
                          {"correction": correction, "type": "one_off"})
        target = f"checkpointer (thread={thread_id})"

    # 4. 通知用户已内化
    return {"internalized": True, "target": target,
            "content": f"[用户偏好 {date_str}] {correction}", "date": date_str}
```

## 输出格式
内化记录:
```json
{
  "internalized": true,
  "target": "SOUL.md (profiles/office-researcher/SOUL.md)",
  "content": "[用户偏好 2026-07-01] 文献检索必须先查 ACM Digital Library",
  "date": "2026-07-01"
}
```

不确定时:
```json
{"need_clarification": true, "question": "这是通用偏好(以后都这样)还是本次指正?"}
```

## 约束
- SOUL.md 只放稳定规则(通用偏好),不塞具体项目经验或一次性指正。
- 不确定时必须问用户,不允许擅自判断后写入 SOUL.md(写入后难以撤销)。
- 通用偏好写入 SOUL.md 时必须带日期标记 `[用户偏好 YYYY-MM-DD]`,便于追溯和后续修订。
- 一次性指正只存当前项目 checkpointer,不污染其他项目。
- 内化完成后必须通知用户(告知目标和内容),让用户知道纠正已被吸收。
