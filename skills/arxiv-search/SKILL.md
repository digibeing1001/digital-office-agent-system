# arxiv-search — arXiv 检索

## 用途
通过 arXiv API 检索预印本论文。支持关键词检索、作者检索、分类检索,可下载 PDF 和提取元数据。

## 触发条件
- 需要检索 arXiv 预印本时。
- 跟踪某领域最新 arXiv 论文时。
- 用户提到"arXiv""预印本""检索"时。

## 工具依赖
```bash
pip install arxiv
```

## 操作步骤
1. 构造查询语句(arXiv 查询语法:ti 标题、au 作者、cat 分类、abs 摘要)。
2. 用 `arxiv.Search` 执行检索。
3. 提取结果:标题、作者、摘要、PDF 链接、发布日期。
4. 可选:下载 PDF。
5. 记录查询语句,保证可复现。

## 调用示例
```python
import arxiv

def search_arxiv(query, max_results=10, sort_by=arxiv.SortCriterion.Relevance):
    """检索 arXiv"""
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=sort_by,
    )
    results = []
    for paper in search.results():
        results.append({
            "title": paper.title,
            "authors": [str(a) for a in paper.authors],
            "summary": paper.summary[:300],
            "published": str(paper.published),
            "arxiv_id": paper.entry_id.split("/")[-1],
            "pdf_url": paper.pdf_url,
            "categories": paper.categories,
            "comment": paper.comment,
        })
    return results

# 关键词检索
results = search_arxiv('ti:"large language model" AND cat:cs.CL', max_results=5)
print(f"检索到 {len(results)} 篇:")
for r in results:
    print(f"\n  {r['title']}")
    print(f"  arXiv: {r['arxiv_id']} | {r['published'][:10]}")
    print(f"  作者: {', '.join(r['authors'][:3])}")
    print(f"  PDF: {r['pdf_url']}")

# 作者检索
author_results = search_arxiv('au:"Yann LeCun"', max_results=3, sort_by=arxiv.SortCriterion.SubmittedDate)

# 下载 PDF
def download_pdf(arxiv_id, save_dir="."):
    search = arxiv.Search(id_list=[arxiv_id])
    for paper in search.results():
        paper.download_pdf(dirpath=save_dir, filename=f"{arxiv_id}.pdf")
        print(f"已下载: {arxiv_id}.pdf")

# 记录查询语句(可复现)
query_log = {
    "query": 'ti:"large language model" AND cat:cs.CL',
    "max_results": 5,
    "sort_by": "Relevance",
    "timestamp": "2026-07-01T12:00:00",
}
print(f"\n查询语句已记录: {query_log['query']}")
```

## 输出格式
- 论文列表(每篇含标题、作者、摘要、arXiv ID、PDF URL、分类、发布日期)。
- 可选:下载的 PDF 文件。
- 查询语句日志(可复现)。

## 约束
- 记录完整查询语句,保证检索可复现。
- arXiv API 有频率限制(建议每次检索间隔 ≥3 秒)。
- 检索结果受 arXiv 索引延迟影响,最新论文可能未及时收录。
