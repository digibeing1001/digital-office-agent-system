# dedup-engine — 去重引擎

## 用途
文献去重,四级去重策略确保不漏不重:DOI 精确去重 → arXiv ID 去重 → 标题精确匹配 → 归一化标题+第一作者+年份 MinHash 近似去重。

## 触发条件
- 批量文献入库前需要去重时。
- 多源检索结果合并时。
- 用户提到"去重""dedup""重复文献"时。

## 工具依赖
```bash
pip install datasketch
```

## 操作步骤
1. 第一级:按 DOI 去重(同一 DOI 视为同一文献)。
2. 第二级:按 arXiv ID 去重(无 DOI 但有 arXiv ID 的)。
3. 第三级:标题精确匹配(大小写+空格归一化后完全相同)。
4. 第四级:归一化标题+第一作者+年份,用 MinHash + LSH 做近似匹配。
5. 输出去重后文献列表 + 重复组。

## 调用示例
```python
from datasketch import MinHash, MinHashLSH
import re
import json

def normalize_title(title):
    """标题归一化"""
    t = title.lower().strip()
    t = re.sub(r'[^a-z0-9\s]', '', t)
    t = re.sub(r'\s+', ' ', t)
    return t

def dedup_by_doi(papers):
    """第一级:DOI 去重"""
    seen_doi = {}
    remaining = []
    for p in papers:
        doi = p.get("doi", "").lower().strip()
        if doi:
            if doi in seen_doi:
                seen_doi[doi].append(p)
            else:
                seen_doi[doi] = [p]
        else:
            remaining.append(p)
    unique = [v[0] for v in seen_doi.values()]
    dup_groups = {k: v for k, v in seen_doi.items() if len(v) > 1}
    return unique, remaining, dup_groups

def dedup_by_arxiv(papers):
    """第二级:arXiv ID 去重"""
    seen = {}
    remaining = []
    for p in papers:
        arxiv = p.get("arxiv_id", "").strip()
        if arxiv:
            if arxiv in seen:
                seen[arxiv].append(p)
            else:
                seen[arxiv] = [p]
        else:
            remaining.append(p)
    return [v[0] for v in seen.values()], remaining

def dedup_by_title(papers):
    """第三级:标题精确匹配"""
    seen = {}
    remaining = []
    for p in papers:
        norm = normalize_title(p.get("title", ""))
        if norm in seen:
            seen[norm].append(p)
        else:
            seen[norm] = [p]
    unique = [v[0] for v in seen.values()]
    return unique

def dedup_by_minhash(papers, threshold=0.8):
    """第四级:归一化标题+作者+年份 MinHash"""
    lsh = MinHashLSH(threshold=threshold, num_perm=128)
    unique = []
    for p in papers:
        key = f"{normalize_title(p.get('title',''))}|{p.get('first_author','').lower()}|{p.get('year','')}"
        mh = MinHash(num_perm=128)
        for word in key.split():
            mh.update(word.encode("utf-8"))
        matches = lsh.query(mh)
        if not matches:
            lsh.insert(p["id"], mh)
            unique.append(p)
    return unique

def full_dedup(papers):
    """四级去重"""
    print(f"输入: {len(papers)} 篇")
    s1, rest1, g1 = dedup_by_doi(papers)
    s2, rest2 = dedup_by_arxiv(rest1)
    s3 = dedup_by_title(s1 + s2 + rest2)
    s4 = dedup_by_minhash(s3)
    print(f"DOI 去重: {len(g1)} 组重复")
    print(f"最终: {len(s4)} 篇(去重 {len(papers)-len(s4)} 篇)")
    return s4

papers = [
    {"id": "p1", "doi": "10.1/x", "title": "Attention Is All You Need", "first_author": "Vaswani", "year": 2017},
    {"id": "p2", "doi": "10.1/X", "title": "Attention is all you need", "first_author": "Vaswani", "year": 2017},
]
result = full_dedup(papers)
```

## 输出格式
- 去重后文献列表。
- 各级去重统计:DOI 重复组数、arXiv 重复数、标题重复数、MinHash 重复数。

## 约束
- 四级去重依次执行,不可跳级。
- MinHash 阈值默认 0.8(标题+作者+年份组合),过高漏报、过低误报。
- 去重保留首次出现的记录,后续重复记录记录到重复组。
