# storm-survey — 综述生成

## 用途
基于 STORM（Stanford Oval）的两阶段综述生成方法，通过"视角引导提问"和"模拟对话"（Wikipedia 作者 vs 主题专家）生成带引用的结构化综述。预写作阶段做 Internet 检索 + 大纲生成，写作阶段做全文 + 引用。

适用于:文献综述初稿生成、领域 survey 撰写、课题立项前的背景调研综述、年度技术进展总结。

## 触发条件
- 课题规划师需要综述某领域现状
- 文献研究员需要生成 survey 初稿
- 用户要求"写综述""survey""总结 X 领域"
- gap-identification 发现需要系统性综述某主题
- deep-research 完成后需要组织成综述格式

## 操作步骤

### 步骤 1:确定综述主题与视角
```python
def define_survey_scope(topic: str, target_length: int = 5000) -> dict:
    """确定综述范围和多视角"""
    # LLM 生成综述大纲的多视角
    perspectives = llm_call(f"""
    主题: {topic}
    生成综述该主题的多个视角（如：历史发展、技术方法、应用场景、挑战与局限、未来方向）。
    每个视角列出 3-5 个关键问题。
    """)
    return {
        "topic": topic,
        "target_length": target_length,
        "perspectives": json.loads(perspectives),
    }
```

### 步骤 2:模拟对话（视角引导提问）
```python
def simulate_dialogue(topic: str, perspective: str, questions: list) -> list:
    """模拟 Wikipedia 作者 vs 主题专家的对话"""
    conversation = []
    for q in questions:
        # 作者提问
        conversation.append({"role": "author", "content": q})
        # 专家回答（基于文献检索）
        answer = research_answer(q, topic)
        conversation.append({"role": "expert", "content": answer["text"], "citations": answer["citations"]})
        # 作者追问（基于回答中的缺口）
        follow_up = generate_follow_up(answer["text"])
        if follow_up:
            conversation.append({"role": "author", "content": follow_up})
            follow_answer = research_answer(follow_up, topic)
            conversation.append({"role": "expert", "content": follow_answer["text"], "citations": follow_answer["citations"]})
    return conversation
```

### 步骤 3:预写作 — 大纲生成
```python
def generate_outline(scope: dict, dialogues: dict) -> dict:
    """基于多视角对话生成综述大纲"""
    all_findings = []
    for perspective, conv in dialogues.items():
        findings = extract_findings_from_dialogue(conv)
        all_findings.append({"perspective": perspective, "findings": findings})
    
    # 聚类成章节
    outline = llm_call(f"""
    基于以下多视角发现，生成综述大纲。
    主题: {scope['topic']}
    发现: {json.dumps(all_findings, ensure_ascii=False)}
    
    要求:
    - 每章节有明确标题和 3-5 个要点
    - 章节间有逻辑递进（不是简单罗列）
    - 每个要点附引用来源
    """)
    return json.loads(outline)
```

### 步骤 4:写作阶段 — 全文 + 引用
```python
def write_survey_sections(outline: dict, dialogues: dict) -> list:
    """按大纲逐章写作"""
    sections = []
    for chapter in outline["chapters"]:
        # 收集该章节相关对话片段
        relevant = find_relevant_dialogues(chapter, dialogues)
        
        # 写作
        text = llm_call(f"""
        章节: {chapter['title']}
        要点: {chapter['points']}
        参考对话: {relevant}
        
        写作要求:
        - 学术综述风格，客观中立
        - 每个观点附引用 [作者, 年份]
        - 章节间过渡自然
        - 不编造引用，只使用参考对话中的来源
        """)
        sections.append({"title": chapter["title"], "text": text, "citations": extract_citations(text)})
    return sections
```

### 步骤 5:整合与润色
```python
def finalize_survey(sections: list, scope: dict) -> str:
    """整合全文，添加摘要和结论"""
    abstract = generate_abstract(sections, scope["topic"])
    conclusion = generate_conclusion(sections, scope["topic"])
    references = aggregate_references(sections)
    
    return f"""
# {scope['topic']} 综述

## 摘要
{abstract}

{format_sections(sections)}

## 结论与展望
{conclusion}

## 参考文献
{format_references(references)}
"""
```

## 输出格式
综述文档（写入 `outputs/survey/<topic>-<date>.md`）:
- **摘要**:300 字内概括综述内容
- **多视角章节**:按视角组织，每章含发现 + 引用
- **结论与展望**:总结现状 + 指出挑战 + 预测方向
- **参考文献**:所有引用的统一列表

## 约束
- 每个观点必须附引用，无引用的观点标注 `[待补引用]`
- 不得编造引用（与 research-integrity-gates hallucinated_citation 协同）
- 综述长度默认 5000 字，最大 20000 字
- 模拟对话每个视角最多 5 轮（防止成本失控）
- 引用来源优先级:学术数据库 > 本地知识库 > Web > getnote 笔记
- 综述初稿必须经过 peer-review skill 审查

## 与现有 skill 的关系
- **与 arxiv-search 协同**:storm-survey 调用 arxiv-search 做文献检索
- **与 paper-qa-rag 协同**:storm-survey 调用 paper-qa-rag 做文献问答
- **与 academic-writing 协同**:storm-survey 生成初稿，academic-writing 做体裁适配
- **与 deep-research 协同**:deep-research 做前置调研，storm-survey 组织成综述
- **与 citation-verification 协同**:综述完成后调用 citation-verification 核查引用

## 依赖工具/API
- LLM API（对话模拟、大纲、写作）
- 学术检索: arxiv-search / paper-qa-rag
- Web 搜索 API
- getnote API（全局指令要求）

## 关键方法论引用
- STORM: Stanford Oval, "Assisting in Writing Wikipedia-like Articles From Scratch with Large Language Models"
- Co-STORM: 人机协作 + 动态思维导图
- GitHub: https://github.com/stanford-oval/storm
