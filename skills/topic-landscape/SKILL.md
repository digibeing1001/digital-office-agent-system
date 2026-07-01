# topic-landscape — 主题景观

## 用途
多角度主题预写作(借鉴 STORM 方法)。输入研究主题后,自动生成多元 persona(不同视角的研究者),每个 persona 提出问题并收集信息,汇总成结构化大纲,为深度写作打基础。

## 触发条件
- 开始一个新研究方向的调研时。
- 需要多视角理解某个主题时。
- 写综述/调研报告需要大纲时。
- 用户提到"主题景观""STORM""预写作""多视角"时。

## 工具依赖
```bash
pip install knowledge-storm
# STORM 需要 LLM + 检索引擎,按其文档配置
```

## 操作步骤
1. 输入研究主题(如 "LLM 的推理能力")。
2. STORM 生成多个 persona(不同视角:方法学者、应用工程师、批评者、历史梳理者)。
3. 每个 persona 围绕主题提问并检索资料。
4. 汇总各 persona 的发现,合成多角度大纲。
5. persona 要多元,覆盖不同立场和方法传统。

## 调用示例
```python
from knowledge_storm import STORM, STORMWikiRunner, STORMWikiRunnerArguments

# 配置(需 LLM 和检索引擎)
args = STORMWikiRunnerArguments(
    output_dir="topic_output",
    max_search_results=5,
    max_conv_turn=3,
)

# 初始化 STORM(需配置 LLM client 和检索器)
# storm = STORM(lm_client=..., rm=...)
# runner = STORMWikiRunner(args, storm)

# 生成主题景观
# topic = "Large Language Models 的推理能力与局限"
# runner.run(topic=topic)

# 手动模拟多 persona(无 STORM 时)
import json

personas = [
    {"name": "方法学者", "focus": "LLM 推理的底层机制是什么?CoT/ToT 原理?"},
    {"name": "应用工程师", "focus": "LLM 推理在实际场景中的效果?延迟/成本权衡?"},
    {"name": "批评者", "focus": "LLM 推理是真推理还是模式匹配?失败案例?"},
    {"name": "历史梳理者", "focus": "推理能力从 GPT-2 到 GPT-4 的演进?关键节点?"},
]

def persona_outline(topic, personas, llm_client):
    """多 persona 生成大纲"""
    sections = []
    for p in personas:
        prompt = f"""你是{p['name']},研究主题"{topic}"。
你的关注点:{p['focus']}
请基于你的视角,列出 3-5 个子问题和要点。"""
        response = llm_client.complete(prompt)
        sections.append({"persona": p["name"], "focus": p["focus"], "content": response})

    outline = {
        "topic": topic,
        "sections": sections,
    }
    return outline

# 生成
# outline = persona_outline("LLM 推理能力", personas, llm_client)
# print(json.dumps(outline, ensure_ascii=False, indent=2))
```

## 输出格式
- 多视角大纲 JSON:每个 persona 一个 section,含关注点和要点。
- 合成的主题大纲(可用于后续深度写作)。

## 约束
- persona 要多元,覆盖不同立场(支持者/批评者/实践者/历史视角)。
- 不可只从一个视角(如纯方法视角)展开。
- persona 提出的问题需具体,不可泛泛。
