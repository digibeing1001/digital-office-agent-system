# cross-run-memory — 跨会话经验记忆

## 用途
新项目启动时按主题相似度检索历史经验,注入 Agent 的 system prompt,让历史经验在新项目中复用。依据 ExpeL 经验检索 + Voyager 技能库复用。

## 触发条件
- 新项目启动时。
- 某个角色开始干活前(首轮产出前)。

## 工具依赖
无额外依赖,使用 BaseStore 向量检索或文件检索:
```bash
pip install langgraph  # BaseStore 提供跨会话经验存储与检索
# 或用文件检索 + 简化相似度(无向量库时)
```

## 操作步骤
1. 识别当前任务主题和角色(从项目 brief / 角色配置读取)。
2. 在 `skills/experience/<agent_id>/` 下按相似度检索 top-5 经验。
3. 注入 Agent 的 system prompt(拼在 system message 末尾)。
4. 记录哪些经验被调用(写入经验调用日志,用于衰减计算)。
5. 经验注入不超过 5 条,避免污染 prompt。

## 调用示例
```python
import os, json, datetime

RETRIEVAL_TOP_K = 5  # 与 scoring_config.experience.retrieval_top_k 一致

def inject_experiences(agent_id, task_topic, system_prompt):
    exp_dir = f"skills/experience/{agent_id}/"
    if not os.path.isdir(exp_dir):
        return system_prompt  # 无经验库直接返回原 prompt

    # 1. 检索 top-k 经验(按相似度,无向量库时用关键词重合)
    candidates = []
    for fn in os.listdir(exp_dir):
        if not fn.endswith(".md"):
            continue
        with open(os.path.join(exp_dir, fn), encoding="utf-8") as f:
            for line in f:
                sim = similarity(task_topic, line)  # 向量相似度或关键词重合
                candidates.append((sim, line.strip(), fn))

    candidates.sort(key=lambda x: x[0], reverse=True)
    top_k = candidates[:RETRIEVAL_TOP_K]

    if not top_k:
        return system_prompt

    # 2. 拼进 system prompt
    exp_block = "\n\n## 历史经验(参考,非硬规则)\n"
    for sim, line, fn in top_k:
        exp_block += f"- {line}  (来源: {fn}, 相似度: {sim:.2f})\n"

    # 3. 记录调用(用于衰减计算)
    log_path = f"skills/experience/{agent_id}/.usage_log.jsonl"
    with open(log_path, "a", encoding="utf-8") as f:
        for sim, line, fn in top_k:
            f.write(json.dumps({
                "experience": line, "source": fn,
                "called_at": datetime.datetime.now().isoformat(),
                "task_topic": task_topic,
            }, ensure_ascii=False) + "\n")

    return system_prompt + exp_block

def similarity(topic, text):
    # 简化:关键词重合率;有向量库时换 embedding cosine
    topic_words = set(topic.lower().split())
    text_words = set(text.lower().split())
    if not topic_words:
        return 0.0
    return len(topic_words & text_words) / len(topic_words)
```

## 输出格式
经验注入列表(top-k insights 拼成文本),追加到 system prompt 末尾:
```
## 历史经验(参考,非硬规则)
- [success] 遇到综述类任务,应该先查近 2 年 survey 再查原文  (来源: literature-review.md, 相似度: 0.82)
- [failure] 遇到新颖性评估,不要只凭 LLM 自评,必须做文献比对  (来源: scoring.md, 相似度: 0.71)
```

同时写入调用日志 `skills/experience/<agent_id>/.usage_log.jsonl`:
```json
{"experience": "...", "source": "literature-review.md", "called_at": "2026-07-01T10:00:00", "task_topic": "文献综述"}
```

## 约束
- 经验注入不超过 5 条(与 `scoring_config.experience.retrieval_top_k` 一致),避免污染 prompt。
- 长期不调用的经验降权(衰减):按 `.usage_log.jsonl` 的 `called_at` 计算,90 天未被调用的经验权重减半。
- 注入的经验标注"参考,非硬规则",Agent 不应盲目套用,需结合当前任务判断。
- 经验检索按相似度排序,相似度过低(< 0.3)的经验不注入,避免噪声。
- 调用日志必须记录,否则无法做衰减;衰减由 experience-extraction 定期执行。
