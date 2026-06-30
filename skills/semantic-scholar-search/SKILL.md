# semantic-scholar-search — Semantic Scholar 检索

## 用途
通过 Semantic Scholar(S2)API 检索文献,提取引用网络、影响力指标、论文详情。S2 提供结构化的引用关系数据,适合构建引文网络和影响力分析。

## 触发条件
- 需要检索论文及引用网络时。
- 需要获取论文的影响力指标(引用数、influential citations)时。
- 用户提到"Semantic Scholar""S2""引用网络""影响力"时。

## 工具依赖
```bash
pip install semanticscholar
```

## 操作步骤
1. 输入查询(关键词 / DOI / arXiv ID / S2 paperId)。
2. 用 S2 API 检索,提取论文详情。
3. 可选:拉取引用(citations)和被引(references)关系。
4. 提取影响力指标:引用数、influential citation count。
5. 记录 API 限流,超限时退避重试。

## 调用示例
```python
from semanticscholar import SemanticScholar
import time

s2 = SemanticScholar()

def search_papers(query, limit=10, fields=None):
    """关键词检索"""
    if fields is None:
        fields = ["title", "authors", "year", "abstract",
                  "citationCount", "influentialCitationCount", "venue"]
    results = s2.search_paper(query, limit=limit, fields=fields)
    papers = []
    for p in results:
        papers.append({
            "paper_id": p.paperId,
            "title": p.title,
            "authors": [a.name for a in (p.authors or [])],
            "year": p.year,
            "venue": p.venue,
            "citation_count": p.citationCount,
            "influential_citations": p.influentialCitationCount,
            "abstract": (p.abstract or "")[:200],
        })
        time.sleep(0.5)  # 遵守限流
    return papers

def get_paper_detail(paper_id):
    """获取单篇论文详情 + 引用关系"""
    paper = s2.get_paper(paper_id, fields=[
        "title", "authors", "year", "abstract",
        "citationCount", "influentialCitationCount",
        "references", "citations"
    ])
    return paper

def get_high_influence_papers(query, top_k=5):
    """找高影响力论文"""
    papers = search_papers(query, limit=20)
    # 按 influential citation 排序
    papers.sort(key=lambda x: x.get("influential_citations", 0), reverse=True)
    print(f"高影响力论文 Top-{top_k}:")
    for p in papers[:top_k]:
        print(f"  [{p['influential_citations']} influential] {p['title'][:60]}")
    return papers[:top_k]

# 执行
results = search_papers("retrieval augmented generation", limit=10)
print(f"检索到 {len(results)} 篇:")
for r in results:
    print(f"  [{r['citation_count']} cites] {r['title'][:60]}")

# 高影响力论文
get_high_influence_papers("retrieval augmented generation", top_k=5)

# 按 DOI 查
# paper = get_paper_detail("DOI:10.1145/3442188.3445922")
```

## 输出格式
- 论文列表(含引用数、influential citations、venue)。
- 单篇论文详情(含引用关系)。
- 高影响力论文排序。

## 约束
- 记录 API 限流,请求间 sleep ≥0.5s,S2 有每秒/每日配额。
- influentialCitationCount 是 S2 特有指标,反映"实质性引用",非总引用数。
- 大规模拉取引用网络需分批,不可一次请求过大数据。
