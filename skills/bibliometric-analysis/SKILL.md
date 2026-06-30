# bibliometric-analysis — 文献计量

## 用途
文献计量分析:发文量趋势、年增长率、引文集中度(H 指数、G 指数),标出"增长且未饱和"的研究方向,为选题提供数据支撑。

## 触发条件
- 选题前需要了解领域发文趋势时。
- 需要判断某方向是否已饱和时。
- 用户提到"文献计量""发文趋势""H 指数""bibliometric"时。

## 工具依赖
```bash
pip install pybibliometrics
# pybibliometrics 需要 Scopus API key
```

## 操作步骤
1. 输入关键词或领域。
2. 检索相关文献(Scopus / S2 / Crossref)。
3. 统计发文量年增长率。
4. 算引文集中度(H 指数、被引集中度)。
5. 标出"增长且未饱和"方向(发文量上升 + 引文集中度不高)。

## 调用示例
```python
from pybibliometrics import Scopus
import pandas as pd
import numpy as np

# 配置(需 Scopus API key)
# scopus = Scopus(api_key="YOUR_KEY")

def analyze_trend(papers):
    """分析发文量趋势"""
    df = pd.DataFrame(papers)
    yearly = df.groupby("year").size().reset_index(name="count")
    yearly["growth_rate"] = yearly["count"].pct_change() * 100
    return yearly

def calc_h_index(citations):
    """计算 H 指数"""
    citations_sorted = sorted(citations, reverse=True)
    h = 0
    for i, c in enumerate(citations_sorted, 1):
        if c >= i:
            h = i
        else:
            break
    return h

def find_emerging_directions(yearly_stats, h_index, total_papers):
    """标出增长且未饱和方向"""
    recent_growth = yearly_stats["growth_rate"].tail(3).mean()
    saturation = h_index / max(total_papers, 1)  # 引文集中度

    verdict = []
    if recent_growth > 10:
        verdict.append("发文量增长")
    else:
        verdict.append("发文量平稳/下降")
    if saturation < 0.1:
        verdict.append("引文分散,尚未形成核心 clique → 未饱和")
    else:
        verdict.append("引文集中,可能已饱和")
    return verdict

# 模拟数据
papers = [
    {"year": 2020, "citations": 120},
    {"year": 2021, "citations": 85},
    {"year": 2022, "citations": 60},
    {"year": 2023, "citations": 45},
    {"year": 2024, "citations": 30},
]

yearly = analyze_trend(papers)
print("=== 发文量趋势 ===")
print(yearly.to_string(index=False))

h = calc_h_index([p["citations"] for p in papers])
print(f"\nH 指数: {h}")

verdict = find_emerging_directions(yearly, h, len(papers))
print("\n=== 方向判断 ===")
for v in verdict:
    print(f"  - {v}")
```

## 输出格式
- 发文量趋势表(年份、数量、增长率)。
- H 指数 / 引文集中度。
- 方向判断:增长且未饱和 / 已饱和。

## 约束
- 数据来自公开数据库(Scopus/S2/Crossref),不可凭印象。
- "未饱和"判断需同时满足:发文量上升 + 引文集中度低,单一指标不足以下结论。
- 增长率需看多年趋势(≥3 年),不可凭单年波动下结论。
