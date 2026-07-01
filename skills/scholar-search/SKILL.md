# scholar-search — Google Scholar 检索

## 用途
通过 Google Scholar 检索文献,提取论文信息(标题、作者、引用数、摘要片段)。使用 scholarly 库访问,注意反爬限制。

## 触发条件
- 需要检索 Google Scholar 时。
- 需要查看论文的 Google Scholar 引用数时。
- 用户提到"Google Scholar""scholarly""引用数"时。

## 工具依赖
```bash
pip install scholarly
# 建议配合代理使用,避免被 Google 封 IP
```

## 操作步骤
1. 输入关键词或论文标题。
2. 用 `scholarly.search_pubs()` 检索。
3. 提取:标题、作者、年份、venue、引用数、摘要片段。
4. 可选:用 `scholarly.search_author()` 查作者信息。
5. 注意反爬:设置代理、控制频率、遇 CAPTCHA 退避。

## 调用示例
```python
from scholarly import scholarly
import json
import time

def search_scholar(query, max_results=5):
    """检索 Google Scholar"""
    results = []
    search_gen = scholarly.search_pubs(query)
    for i, paper in enumerate(search_gen):
        if i >= max_results:
            break
        bib = paper.get("bib", {})
        results.append({
            "title": bib.get("title", ""),
            "author": bib.get("author", []),
            "year": bib.get("pub_year", ""),
            "venue": bib.get("venue", ""),
            "abstract": bib.get("abstract", "")[:300],
            "citations": paper.get("num_citations", 0),
            "scholar_id": paper.get("author_id", ""),
            "url": paper.get("pub_url", ""),
        })
        time.sleep(2)  # 反爬:每次检索间隔
    return results

# 关键词检索
results = search_scholar("transformer attention mechanism", max_results=5)
print(f"检索到 {len(results)} 篇:")
for r in results:
    print(f"\n  {r['title']}")
    print(f"  引用数: {r['citations']} | {r['year']}")
    print(f"  作者: {', '.join(r['author'][:3])}")

# 作者检索
def search_author(name):
    """查作者信息"""
    author = scholarly.search_author(name)
    if author:
        author_data = scholarly.fill(next(author))
        return {
            "name": author_data.get("name", ""),
            "affiliation": author_data.get("affiliation", ""),
            "interests": author_data.get("interests", []),
            "citedby": author_data.get("citedby", 0),
            "hindex": author_data.get("hindex", 0),
        }
    return None

# 配置代理(避免被封)
from scholarly import scholarly, ProxyGenerator
pg = ProxyGenerator()
# pg.FreeProxies()  # 免费代理(不稳定)
# pg.ScraperAPI("YOUR_KEY")  # 付费代理更稳定
# scholarly.use_proxy(pg)

# 注意:Google Scholar 有严格反爬,建议:
# 1. 使用代理轮换
# 2. 每次请求间隔 3-5 秒
# 3. 遇 CAPTCHA 时暂停并更换 IP
```

## 输出格式
- 论文列表(标题、作者、年份、venue、引用数、摘要片段)。
- 可选:作者画像(机构、研究方向、H 指数)。

## 约束
- 注意反爬限制:每次请求间隔 ≥3 秒,建议使用代理。
- Google Scholar 引用数为近似值,可能与实际有偏差。
- 遇 CAPTCHA 必须暂停,不可强行突破。
- scholarly 库可能因 Google 页面改版而失效,需关注版本更新。
