# paper-qa-rag — 科学文献高精度 RAG

## 用途
基于 PaperQA2 构建科学文献问答与核查能力，在科学问答、文献总结、矛盾检测上达到超人表现。支持自动获取论文元数据（含引用数和撤稿检查）、本地 PDF 全文检索、多模态图表理解。作为资料员和文献研究员的知识库后端。

适用于:文献综述核查、claim 文献支撑验证、矛盾证据检测、撤稿论文排查、跨论文知识问答。

## 触发条件
- 文献研究员需要回答"关于 X 方法，现有文献怎么说"
- 资料员定时采集文献后需要建立可问答的知识库
- research-integrity-gates 的 retracted_source_dependency 门控需要撤稿检查
- claim-verification 需要找到支撑/反驳某 claim 的文献证据
- 用户要求"查文献""找证据""这个 claim 有没有文献支撑"

## 操作步骤

### 步骤 1:初始化 PaperQA2
```bash
pip install paper-qa
```

```python
from paperqa import Docs, ask

# 初始化文档库
docs = Docs()

# 添加已有 PDF 文献
import glob
for pdf_path in glob.glob("knowledge/spaces/literature/**/*.pdf", recursive=True):
    docs.add(pdf_path)
```

### 步骤 2:文献问答
```python
def answer_literature_question(question: str, docs: Docs) -> dict:
    """回答科学文献问题，返回答案 + 引用"""
    answer = ask(question, docs)
    return {
        "question": question,
        "answer": answer.answer,
        "citations": [
            {"text": c.text, "source": c.doc.name, "page": c.page}
            for c in answer.citations
        ],
        "confidence": answer.confidence,
    }
```

### 步骤 3:撤稿检查
```python
def check_retraction(doi: str) -> dict:
    """通过 Crossref 检查论文是否已撤稿"""
    import requests
    url = f"https://api.crossref.org/works/{doi}"
    resp = requests.get(url, headers={"User-Agent": "digital-office/1.0"})
    work = resp.json()["message"]
    is_retracted = work.get("is-referenced-by-count", 0) == 0 and "retraction" in str(work.get("title", "")).lower()
    # 更准确的检查：查 update-to 字段
    updates = work.get("updated-by", [])
    for update in updates:
        if "retraction" in update.get("type", "").lower():
            return {"retracted": True, "doi": doi, "update_type": "retraction"}
    return {"retracted": False, "doi": doi}
```

### 步骤 4:矛盾检测
```python
def detect_contradictions(claims: list, docs: Docs) -> list:
    """检测多个 claim 之间的矛盾"""
    contradictions = []
    for i, c1 in enumerate(claims):
        for c2 in claims[i+1:]:
            prompt = f"以下两个 claim 是否矛盾？\nA: {c1}\nB: {c2}\n回答 YES/NO 并说明理由。"
            result = ask(prompt, docs)
            if "YES" in result.answer.upper()[:10]:
                contradictions.append({
                    "claim_a": c1, "claim_b": c2,
                    "reason": result.answer, "evidence": result.citations
                })
    return contradictions
```

### 步骤 5:元数据增强
```python
def enrich_metadata(paper_title: str) -> dict:
    """获取论文元数据（引用数、撤稿标记、发表状态）"""
    from semanticscholar import SemanticScholar
    s2 = SemanticScholar()
    results = s2.search_paper(paper_title, limit=1)
    if results:
        p = results[0]
        return {
            "title": p.title,
            "year": p.year,
            "citation_count": p.citationCount,
            "influential_citation_count": p.influentialCitationCount,
            "venue": p.venue,
            "open_access_pdf": p.openAccessPdf.url if p.openAccessPdf else None,
            "fields_of_study": p.fieldsOfStudy,
        }
    return {"error": "not found"}
```

## 输出格式
```json
{
  "question": "LoRA 在低资源场景下的效果如何？",
  "answer": "LoRA 在参数量减少 10000x 的情况下...",
  "citations": [
    {"text": "LoRA achieves comparable performance...", "source": "hu2021lora.pdf", "page": 5}
  ],
  "confidence": 0.92,
  "retraction_warnings": [],
  "contradictions": []
}
```

## 约束
- 所有答案必须附带引用（无引用的答案标记为"低置信度"）
- 撤稿论文的答案必须标注警告，不得作为唯一依据
- 矛盾检测需至少 2 个独立来源才下结论
- 元数据获取失败时降级为本地 PDF 检索，不得跳过
- PDF 解析失败时记录到 failure-mode-archiving，不静默跳过

## 与现有 skill 的关系
- **与 arxiv-search 互补**:arxiv-search 负责检索获取，paper-qa-rag 负责问答核查
- **与 citation-verification 协同**:citation-verification 验证引用存在性，paper-qa-rag 提供内容核查
- **与 retraction-check 协同**:paper-qa-rag 内置撤稿检查，retraction-check 是专项深度检查

## 依赖工具/API
- paper-qa: `pip install paper-qa`
- semanticscholar: `pip install semanticscholar`
- Crossref API（撤稿检查）
- 本地 PDF 存储: knowledge/spaces/literature/

## 关键方法论引用
- PaperQA2: https://github.com/Future-House/paper-qa
- "PaperQA2: An agent for answering scientific questions", Future-House, 2024
