# pdf-parsing — PDF 解析

## 用途
PDF 全文结构化解析。通过 GROBID REST API 把 PDF 解析为结构化输出(标题、摘要、章节、引用、表格),pdfplumber 补充表格提取,供后续文献分析使用。

## 触发条件
- 需要从 PDF 提取结构化内容(章节/引用/表格)时。
- 文献入库前需要解析全文时。
- 用户提到"PDF 解析""GROBID""全文提取"时。

## 工具依赖
```bash
pip install pdfplumber requests
# GROBID(Docker):
docker run --rm -p 8070:8070 lfoppiano/grobid:0.8.1
```

## 操作步骤
1. 确保 GROBID Docker 容器运行(端口 8070)。
2. 把 PDF 发送到 GROBID `/api/processFulltextDocument` 接口。
3. GROBID 返回 TEI XML,解析出标题、摘要、章节、引用列表。
4. 用 pdfplumber 补充提取表格(复杂表格 GROBID 可能漏)。
5. 输出结构化 JSON。

## 调用示例
```python
import requests
import pdfplumber
import xml.etree.ElementTree as ET
import json

GROBID_URL = "http://localhost:8070/api/processFulltextDocument"

def parse_with_grobid(pdf_path):
    """用 GROBID 解析 PDF 全文"""
    with open(pdf_path, "rb") as f:
        response = requests.post(
            GROBID_URL,
            files={"input": f},
            timeout=120
        )
    if response.status_code != 200:
        raise Exception(f"GROBID 错误: {response.status_code}")
    return response.text  # TEI XML

def extract_tei_fields(tei_xml):
    """从 TEI XML 提取结构化字段"""
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    root = ET.fromstring(tei_xml)

    # 标题
    title_el = root.find(".//tei:titleStmt/tei:title", ns)
    title = title_el.text if title_el is not None else ""

    # 摘要
    abstract_el = root.find(".//tei:abstract", ns)
    abstract = " ".join(t.text or "" for t in abstract_el.iter() if t.text) if abstract_el is not None else ""

    # 章节
    sections = []
    for div in root.findall(".//tei:body//tei:div", ns):
        head = div.find("tei:head", ns)
        sec_title = head.text if head is not None else ""
        sec_text = " ".join(p.text or "" for p in div.findall(".//tei:p", ns) if p.text)
        if sec_title or sec_text:
            sections.append({"title": sec_title, "text": sec_text[:500]})

    # 引用列表
    references = []
    for bib in root.findall(".//tei:listBibl/tei:biblStruct", ns):
        ref_title = bib.find(".//tei:title", ns)
        references.append(ref_title.text if ref_title is not None else "")

    return {
        "title": title,
        "abstract": abstract,
        "sections": sections,
        "references": references,
    }

def extract_tables(pdf_path):
    """用 pdfplumber 提取表格"""
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            for table in page.extract_tables():
                tables.append({"page": i + 1, "rows": table})
    return tables

# 执行
tei = parse_with_grobid("paper.pdf")
parsed = extract_tei_fields(tei)
parsed["tables"] = extract_tables("paper.pdf")

print(f"标题: {parsed['title']}")
print(f"章节数: {len(parsed['sections'])}")
print(f"引用数: {len(parsed['references'])}")
print(f"表格数: {len(parsed['tables'])}")

with open("parsed_paper.json", "w", encoding="utf-8") as f:
    json.dump(parsed, f, ensure_ascii=False, indent=2)
```

## 输出格式
- 结构化 JSON:标题、摘要、章节列表(标题+正文)、引用列表、表格列表。

## 约束
- GROBID 需要 Docker 环境,无 Docker 无法运行。
- GROBID 解析失败的 PDF 回退到 pdfplumber 纯文本提取,但结构信息会丢失。
- 表格提取以 pdfplumber 为补充,两者结果合并。
