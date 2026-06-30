# metadata-extraction — 元数据抽取

## 用途
从 DOI 或文献标识符抽取结构化元数据(标题、作者、年份、venue、引用数等),补全文献库的元数据信息,统一输出标准格式。

## 触发条件
- 拿到一批 DOI 需要补全文献信息时。
- 文献入库前需要元数据时。
- 用户提到"元数据""DOI""Crossref""habanero"时。

## 工具依赖
```bash
pip install crossrefapi habanero
```

## 操作步骤
1. 输入 DOI(单个或批量)。
2. 用 crossrefapi 查询 Crossref API。
3. 提取标准字段:title、authors、year、venue、volume、issue、pages、DOI。
4. 补全缺失字段(可结合 habanero 查其他源)。
5. 输出标准 JSON,标注缺失字段。

## 调用示例
```python
from crossref.restful import Works
import json

works = Works()

def extract_by_doi(doi):
    """通过 DOI 抽取元数据"""
    try:
        record = works.doi(doi)
    except Exception as e:
        return {"doi": doi, "error": str(e), "complete": False}

    # 解析作者
    authors = []
    for author in record.get("author", []):
        given = author.get("given", "")
        family = author.get("family", "")
        authors.append(f"{family}, {given}".strip(", "))

    # 解析年份
    year = None
    for date_field in ["published-print", "published-online", "created"]:
        if date_field in record and "date-parts" in record[date_field]:
            year = record[date_field]["date-parts"][0][0]
            break

    meta = {
        "doi": doi,
        "title": record.get("title", [""])[0] if record.get("title") else "",
        "authors": authors,
        "year": year,
        "venue": record.get("container-title", [""])[0] if record.get("container-title") else "",
        "volume": record.get("volume", ""),
        "issue": record.get("issue", ""),
        "pages": record.get("page", ""),
        "publisher": record.get("publisher", ""),
        "type": record.get("type", ""),
        "url": record.get("URL", ""),
        "cited_by": record.get("is-referenced-by-count", 0),
    }

    # 标注缺失字段
    missing = [k for k, v in meta.items() if v in ("", None, 0) and k != "cited_by"]
    meta["missing_fields"] = missing
    meta["complete"] = len(missing) == 0
    if missing:
        print(f"⚠️ {doi} 缺失字段: {missing}")
    return meta

# 单个 DOI
result = extract_by_doi("10.1145/3442188.3445922")
print(json.dumps(result, ensure_ascii=False, indent=2))

# 批量处理
dois = [
    "10.1145/3442188.3445922",
    "10.1038/s41586-021-03819-2",
    "10.1126/science.abc1234",  # 假 DOI
]
metadata_list = [extract_by_doi(d) for d in dois]

# 统计完整率
complete_count = sum(1 for m in metadata_list if m.get("complete"))
print(f"\n元数据完整率: {complete_count}/{len(metadata_list)}")
```

## 输出格式
- 标准 JSON:每篇文献含 title、authors、year、venue、volume、issue、pages、DOI、cited_by。
- 缺失字段列表 + 完整率统计。

## 约束
- 元数据不完整时必须标注缺失字段,不可静默忽略。
- 作者格式统一为 "Family, Given"。
- 年份优先取 published-print,其次 published-online,最后 created。
- DOI 无效时标注 error,不可跳过。
