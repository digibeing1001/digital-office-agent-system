# bibtex-management — BibTeX 管理

## 用途
`.bib` 文件的读写、去重、格式校验。自动检测重复条目(DOI/key 重复)、缺失字段、格式错误,保证 `.bib` 文件干净可用。

## 触发条件
- 论文 `.bib` 文件需要清理时。
- 引用条目过多需要去重时。
- 交稿前校验 `.bib` 完整性时。
- 用户提到"bib 管理""去重""校验"时。

## 工具依赖
```bash
pip install bibtexparser
```

## 操作步骤
1. 读取 `.bib` 文件,解析为条目列表。
2. 去重:按 cite key 去重,按 DOI 去重(若有)。
3. 格式校验:检查必填字段(title、author、year、journal/venue)。
4. 标注问题条目(缺失字段、重复)。
5. 写回干净的 `.bib` 文件。

## 调用示例
```python
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter

def load_bib(path):
    parser = BibTexParser(common_strings=True)
    parser.ignore_nonstandard_types = False
    with open(path, encoding="utf-8") as f:
        return bibtexparser.load(f, parser=parser)

def dedup_entries(entries):
    """按 key 和 DOI 去重"""
    seen_keys = set()
    seen_dois = set()
    unique = []
    duplicates = []
    for e in entries:
        key = e.get("ID", "")
        doi = e.get("doi", "").lower().strip()
        if key in seen_keys:
            duplicates.append((key, "重复 key"))
            continue
        if doi and doi in seen_dois:
            duplicates.append((key, f"重复 DOI: {doi}"))
            continue
        seen_keys.add(key)
        if doi:
            seen_dois.add(doi)
        unique.append(e)
    return unique, duplicates

def validate_entries(entries):
    """校验必填字段"""
    required = {"title", "author", "year"}
    issues = []
    for e in entries:
        missing = required - set(e.keys())
        if missing:
            issues.append((e.get("ID", "?"), f"缺失字段: {missing}"))
        # 检查 year 格式
        year = e.get("year", "")
        if year and not year.isdigit():
            issues.append((e.get("ID", "?"), f"year 格式异常: {year}"))
    return issues

def save_bib(path, entries):
    writer = BibTexWriter()
    writer.indent = "  "
    db = bibtexparser.bibdatabase.BibDatabase()
    db.entries = entries
    with open(path, "w", encoding="utf-8") as f:
        f.write(writer.write(db))

# 执行
bib_db = load_bib("references.bib")
print(f"原始条目数: {len(bib_db.entries)}")

unique, dups = dedup_entries(bib_db.entries)
print(f"去重: 删除 {len(dups)} 条")
for key, reason in dups:
    print(f"  - {key}: {reason}")

issues = validate_entries(unique)
if issues:
    print(f"\n校验问题 ({len(issues)} 条):")
    for key, issue in issues:
        print(f"  - {key}: {issue}")
else:
    print("\n校验通过,无缺失字段")

save_bib("references_clean.bib", unique)
print(f"\n已写回 references_clean.bib ({len(unique)} 条)")
```

## 输出格式
- 去重后的 `.bib` 文件。
- 去重报告:重复条目列表及原因。
- 校验报告:问题条目列表及缺失字段。

## 约束
- 不手动维护 `.bib`,统一用 bibtexparser 程序化处理。
- 去重后必须保留一份原始备份(`.bib.original`)。
- 有缺失必填字段的条目标注但不自动删除,需人工确认。
