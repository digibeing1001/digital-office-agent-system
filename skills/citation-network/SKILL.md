# citation-network — 引文网络

## 用途
构建本地引文图。以核心论文为种子,通过 Semantic Scholar API 拉取引用(citing)和被引(cited)关系,用 NetworkX 建图,支持查询奠基论文、影响链、引用簇。

## 触发条件
- 需要分析某篇论文的引用网络时。
- 需要找奠基论文或影响链时。
- 用户提到"引文网络""citation graph""引用关系"时。

## 工具依赖
```bash
pip install networkx semanticscholar
```

## 操作步骤
1. 输入核心论文(DOI / arXiv ID / S2 paperId)。
2. 用 S2 API 拉 citing(谁引用了它)和 cited(它引用了谁)。
3. 用 NetworkX 建有向图(citing → paper → cited)。
4. 支持查询:奠基论文(入度高)、影响链(路径搜索)、引用簇(社区发现)。
5. 记录 API 限流,超限时退避重试。

## 调用示例
```python
import networkx as nx
from semanticscholar import SemanticScholar
import time

s2 = SemanticScholar()

def get_paper(paper_id):
    """获取论文及其引用关系"""
    paper = s2.get_paper(paper_id)
    return paper

def build_citation_graph(seed_paper_id, depth=1):
    """以 seed 论文为中心建引文图"""
    G = nx.DiGraph()
    paper = get_paper(seed_paper_id)
    G.add_node(paper.paperId, title=paper.title, year=paper.year)

    # 拉被引文献(它引用了谁)
    try:
        for ref in paper.references[:50]:  # 限流,只取前 50
            if ref.paperId:
                G.add_node(ref.paperId, title=ref.title, year=ref.year)
                G.add_edge(paper.paperId, ref.paperId, type="cites")
            time.sleep(0.5)  # 遵守 API 限流
    except Exception as e:
        print(f"拉被引文献出错: {e}")

    # 拉引用文献(谁引用了它)
    try:
        citations = s2.get_paper_citations(seed_paper_id)
        for cit in list(citations)[:50]:
            c = cit.citingPaper
            if c.paperId:
                G.add_node(c.paperId, title=c.title, year=c.year)
                G.add_edge(c.paperId, paper.paperId, type="cites")
            time.sleep(0.5)
    except Exception as e:
        print(f"拉引用文献出错: {e}")

    return G

def find_foundational_papers(G, top_k=5):
    """找奠基论文:被引次数最高"""
    in_deg = dict(G.in_degree())
    sorted_nodes = sorted(in_deg.items(), key=lambda x: x[1], reverse=True)
    print("奠基论文(被引最多):")
    for node_id, deg in sorted_nodes[:top_k]:
        title = G.nodes[node_id].get("title", "N/A")
        print(f"  [{deg}次] {title[:60]}")

def find_influence_chain(G, src, dst):
    """找影响链:从 src 到 dst 的路径"""
    try:
        paths = list(nx.all_shortest_paths(G, src, dst))
        print(f"影响链({len(paths)} 条最短路径):")
        for path in paths[:3]:
            titles = [G.nodes[n].get("title", "?")[:30] for n in path]
            print("  → ".join(titles))
    except nx.NetworkXNoPath:
        print("无影响链")

# 执行
G = build_citation_graph("10.1145/3442188.3445922", depth=1)
print(f"引文图: {G.number_of_nodes()} 节点, {G.number_of_edges()} 边")
find_foundational_papers(G)
```

## 输出格式
- NetworkX 有向图对象(可序列化为 GraphML)。
- 奠影论文列表(按入度排序)。
- 影响链(路径列表)。

## 约束
- 记录 API 限流,请求间 sleep ≥0.5s,超限退避重试。
- 大规模引用网络需分层拉取(depth 控制),不可一次全拉。
- S2 API 有每日配额,需记录剩余配额。
