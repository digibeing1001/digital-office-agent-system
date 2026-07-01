# citation-generation — 引用生成

## 用途
从 DOI 自动生成指定格式的引用(BibTeX / APA / MLA / Chicago),写入 `.bib` 文件或正文引用,杜绝手动编引用格式出错。

## 触发条件
- 拿到 DOI 需要生成引用时。
- 写论文需要往 `.bib` 添加新引用时。
- 用户提到"引用生成""BibTeX""APA""citation"时。

## 工具依赖
```bash
pip install crossrefapi
```

## 操作步骤
1. 输入 DOI。
2. 用 crossrefapi 查询文献元数据。
3. 根据目标格式(BibTeX/APA/MLA/Chicago)生成引用文本。
4. 若为 BibTeX,追加写入 `.bib` 文件。
5. 若为正文引用,生成 `\cite{}` 格式。

## 调用示例
```python
from crossref.restful import Works
import re

works = Works()

def fetch_metadata(doi):
    record = works.doi(doi)
    authors = []
    for a in record.get("author", []):
        given = a.get("given", "")
        family = a.get("family", "")
        authors.append({"family": family, "given": given})
    year = None
    for df in ["published-print", "published-online", "created"]:
        if df in record and "date-parts" in record[df]:
            year = record[df]["date-parts"][0][0]
            break
    return {
        "doi": doi,
        "title": record.get("title", [""])[0],
        "authors": authors,
        "year": year,
        "venue": record.get("container-title", [""])[0] if record.get("container-title") else "",
        "volume": record.get("volume", ""),
        "issue": record.get("issue", ""),
        "pages": record.get("page", ""),
        "publisher": record.get("publisher", ""),
    }

def to_bibtex(meta):
    """生成 BibTeX"""
    key = re.sub(r'[^a-zA-Z]', '', meta["authors"][0]["family"] if meta["authors"] else "anon") + str(meta["year"] or "")
    authors_str = " and ".join(
        f"{a['family']}, {a['given']}" for a in meta["authors"]
    )
    entry = f"""@article{{{key},
  title = {{{meta['title']}}},
  author = {{{authors_str}}},
  year = {{{meta['year']}}},
  journal = {{{meta['venue']}}},
  volume = {{{meta['volume']}}},
  number = {{{meta['issue']}}},
  pages = {{{meta['pages']}}},
  doi = {{{meta['doi']}}},
  publisher = {{{meta['publisher']}}}
}}"""
    return key, entry

def to_apa(meta):
    """生成 APA 格式"""
    a = meta["authors"]
    if a:
        first = f"{a[0]['family']}, {a[0]['given'][0]}."
        et = ", ".join(f"{x['family']}, {x['given'][0]}." for x in a[1:3])
        auth_str = first + (" & " + et if et else "")
        if len(a) > 3:
            auth_str += " et al."
    else:
        auth_str = "Anonymous"
    return f"{auth_str} ({meta['year']}). {meta['title']}. {meta['venue']}, {meta['volume']}({meta['issue']}), {meta['pages']}."

# 使用
meta = fetch_metadata("10.1145/3442188.3445922")
key, bib = to_bibtex(meta)
print("=== BibTeX ===")
print(bib)
print("\n=== APA ===")
print(to_apa(meta))

# 追加写入 .bib 文件
with open("references.bib", "a", encoding="utf-8") as f:
    f.write("\n\n" + bib + "\n")
print(f"\n已写入 references.bib (key={key})")
```

## 输出格式
- BibTeX 条目字符串(可直接写入 `.bib`)。
- APA/MLA/Chicago 格式的引用文本。
- BibTeX cite key。

## 约束
- 不手动编引用格式,统一从 DOI 通过 API 生成。
- 作者名、年份、venue 以 Crossref 返回为准,不可手填。
- 写入 `.bib` 前检查 cite key 是否已存在,避免重复。
