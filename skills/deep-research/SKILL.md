# deep-research — 树状递归深度研究

## 用途
基于 gpt-researcher 的 Planner + Execution 双代理架构和 Deep Research 树状递归探索模式，对复杂研究主题进行多轮、多源、多视角的深度调研，生成带引用的结构化研究报告。支持本地文档研究、MCP 集成、多 Agent 协作。

适用于:课题规划前的领域深度调研、文献综述的前置资料收集、竞品/技术方案的深度对比、行业趋势的树状探索。

## 触发条件
- 课题规划师需要在立项前做领域深度调研
- 文献研究员需要生成带引用的综述初稿
- 用户要求"深度调研""deep research""全面分析 X"
- gap-identification 发现知识缺口需要补充调研
- 多源信息需要交叉验证后生成综合报告

## 操作步骤

### 步骤 1:规划研究问题树
```python
def build_research_tree(topic: str, max_depth: int = 3, max_branches: int = 5) -> dict:
    """构建树状研究问题树"""
    # 根节点是主问题
    tree = {"question": topic, "children": [], "depth": 0, "status": "pending"}
    
    # LLM 分解为子问题
    sub_questions = llm_decompose(topic, max_branches)
    for sq in sub_questions:
        node = {"question": sq, "children": [], "depth": 1, "status": "pending"}
        tree["children"].append(node)
        if max_depth > 1:
            # 递归分解
            sub_sq = llm_decompose(sq, max_branches // 2)
            for ssq in sub_sq:
                node["children"].append({
                    "question": ssq, "children": [], "depth": 2, "status": "pending"
                })
    return tree
```

### 步骤 2:并行执行研究
```python
import asyncio

async def execute_research(tree: dict, sources: list) -> dict:
    """并行执行树状研究，每个叶子节点独立检索"""
    async def research_node(node):
        if node["children"]:
            # 非叶子节点：递归
            results = await asyncio.gather(*[research_node(c) for c in node["children"]])
            node["synthesis"] = synthesize(results)
            node["status"] = "done"
        else:
            # 叶子节点：执行检索
            node["raw_findings"] = await search_and_extract(node["question"], sources)
            node["status"] = "done"
        return node
    
    return await research_node(tree)
```

### 步骤 3:多源检索与提取
```python
async def search_and_extract(query: str, sources: list) -> list:
    """从多个源并行检索并提取关键信息"""
    findings = []
    
    # Web 搜索
    if "web" in sources:
        web_results = await web_search(query)
        findings.extend(extract_key_points(web_results))
    
    # 学术搜索
    if "academic" in sources:
        from semanticscholar import SemanticScholar
        s2 = SemanticScholar()
        papers = s2.search_paper(query, limit=10)
        for p in papers:
            findings.append({
                "source": p.title, "year": p.year,
                "key_finding": p.abstract, "citation_count": p.citationCount
            })
    
    # 本地知识库
    if "local" in sources:
        local_results = search_local_kb(query)
        findings.extend(local_results)
    
    # getnote 笔记库
    if "getnote" in sources:
        note_results = search_getnote(query)
        findings.extend(note_results)
    
    return findings
```

### 步骤 4:综合与去重
```python
def synthesize(node_results: list) -> dict:
    """综合多个子节点的研究结果"""
    all_findings = []
    for r in node_results:
        all_findings.extend(r.get("raw_findings", r.get("synthesis", {}).get("findings", [])))
    
    # 去重（语义相似度 > 0.85）
    unique = dedup_by_similarity(all_findings, threshold=0.85)
    
    # 按主题聚类
    clusters = cluster_by_topic(unique)
    
    return {
        "findings_count": len(unique),
        "clusters": clusters,
        "key_insights": extract_top_insights(clusters, top_k=5),
        "contradictions": detect_contradictions(unique),
    }
```

### 步骤 5:生成研究报告
```python
def generate_report(tree: dict, format: str = "markdown") -> str:
    """生成带引用的结构化研究报告"""
    report = {
        "title": f"深度调研报告: {tree['question']}",
        "executive_summary": tree.get("synthesis", {}).get("key_insights", []),
        "sections": [],
        "references": [],
        "contradictions": tree.get("synthesis", {}).get("contradictions", []),
    }
    
    for child in tree["children"]:
        section = {
            "heading": child["question"],
            "findings": child.get("synthesis", child.get("raw_findings", [])),
            "sub_sections": [
                {"heading": gc["question"], "findings": gc.get("raw_findings", [])}
                for gc in child["children"]
            ]
        }
        report["sections"].append(section)
    
    if format == "markdown":
        return render_markdown(report)
    return json.dumps(report, ensure_ascii=False, indent=2)
```

## 输出格式
研究报告（写入 `outputs/research/<topic>-<date>.md`）:
- **执行摘要**:3-5 个关键洞察
- **章节**:按研究问题树组织，每章含发现 + 引用
- **矛盾点**:不同来源的矛盾发现及分析
- **参考文献**:所有引用来源列表
- **研究元数据**:检索源、深度、分支数、总发现数

## 约束
- 每个发现必须附引用来源（URL/论文/笔记）
- 矛盾发现必须显式标注，不得隐去
- 树状深度默认 3 层，最大 5 层（防止失控）
- 单次研究最多检索 100 个源（与 cost-control rate_limiting 对齐）
- getnote 笔记库作为优先源（全局指令）
- 本地知识库优先于 Web 搜索（降低成本）

## 与现有 skill 的关系
- **与 arxiv-search 协同**:deep-research 调用 arxiv-search 做学术检索
- **与 paper-qa-rag 协同**:deep-research 收集资料后，paper-qa-rag 做深度问答
- **与 gap-identification 协同**:deep-research 可填补 gap-identification 发现的知识缺口
- **与 abstract-compression 协同**:deep-research 产出较长，用 abstract-compression 压缩

## 依赖工具/API
- semanticscholar: 学术文献检索
- Web 搜索 API
- getnote API: 笔记库检索（全局指令要求）
- 本地知识库: knowledge/spaces/

## 关键方法论引用
- gpt-researcher: https://github.com/assafelovic/gpt-researcher
- STORM (Stanford): 视角引导提问 + 模拟对话
- Deep Research 树状递归探索模式
