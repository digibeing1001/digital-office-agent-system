# retraction-check — 撤稿专项检查

## 用途
对论文/报告中的所有引用执行专项撤稿检查，通过 Crossref、Retraction Watch、Semantic Scholar 三个独立源核对论文是否已撤稿、是否被表达关注（Expression of Concern）、是否有更正（Correction）。与 `citation-verification`（验证存在性）互补，retraction-check 专项检查撤稿状态。

适用于:投稿前最终核查、research-integrity-gates 的 retracted_source_dependency 门控、综述定稿前的撤稿排查、引用依赖性评估（核心论点是否依赖撤稿论文）。

## 触发条件
- research-integrity-gates 的 retracted_source_dependency 门控触发
- 投稿/提交前的最终核查
- citation-verification 完成后的深度检查
- 用户要求"查撤稿""检查引用是否有撤稿"
- 综述/论文定稿前

## 操作步骤

### 步骤 1:提取所有引用 DOI
```python
def extract_dois_from_references(bib_file: str) -> list:
    """从 BibTeX 文件提取所有 DOI"""
    dois = []
    with open(bib_file, encoding="utf-8") as f:
        for line in f:
            if "doi" in line.lower():
                doi = line.split("doi")[1].split("{")[1].split("}")[0].strip()
                dois.append(doi)
    return dois
```

### 步骤 2:三源撤稿检查
```python
def check_retraction_three_sources(doi: str) -> dict:
    """三源交叉检查撤稿状态"""
    results = {
        "doi": doi,
        "crossref": _check_crossref(doi),
        "retraction_watch": _check_retraction_watch(doi),
        "semantic_scholar": _check_s2_status(doi),
    }
    
    # 综合判定
    any_retracted = any(r.get("retracted") for r in results.values())
    any_concern = any(r.get("expression_of_concern") for r in results.values())
    any_correction = any(r.get("correction") for r in results.values())
    
    return {
        "doi": doi,
        "retracted": any_retracted,
        "expression_of_concern": any_concern,
        "correction": any_correction,
        "sources": results,
        "severity": "critical" if any_retracted else ("warning" if any_concern else ("info" if any_correction else "clean")),
    }
```

### 步骤 3:Crossref 检查
```python
def _check_crossref(doi: str) -> dict:
    """通过 Crossref 检查撤稿标记"""
    import requests
    url = f"https://api.crossref.org/works/{doi}"
    resp = requests.get(url, headers={"User-Agent": "digital-office/1.0"})
    if resp.status_code != 200:
        return {"error": "not_found"}
    work = resp.json()["message"]
    
    # 检查 update-to 字段（撤稿会在这里标记）
    updates = work.get("updated-by", [])
    for update in updates:
        update_type = update.get("type", "").lower()
        if "retraction" in update_type:
            return {"retracted": True, "update_type": update_type, "update_doi": update.get("DOI")}
        if "expression-of-concern" in update_type:
            return {"expression_of_concern": True, "update_type": update_type}
        if "correction" in update_type:
            return {"correction": True, "update_type": update_type}
    
    return {"retracted": False, "clean": True}
```

### 步骤 4:Retraction Watch 检查
```python
def _check_retraction_watch(doi: str) -> dict:
    """通过 Retraction Watch Database 检查"""
    import requests
    # Retraction Watch CSV 数据库
    url = f"https://api.labs.crossref.org/data/retractionwatch?doi={doi}"
    resp = requests.get(url)
    if resp.status_code == 200 and resp.text.strip():
        data = resp.json()
        return {
            "retracted": True,
            "reason": data.get("reason", "unknown"),
            "retraction_date": data.get("retractiondate"),
            "nature": data.get("nature", "unknown"),
        }
    return {"retracted": False, "clean": True}
```

### 步骤 5:依赖性评估
```python
def assess_dependency(retraction_results: list, paper_text: str) -> dict:
    """评估论文对撤稿引用的依赖程度"""
    retracted_dois = [r for r in retraction_results if r["retracted"]]
    if not retracted_dois:
        return {"has_retracted": False, "dependency": "none"}
    
    # 检查撤稿论文在正文中的引用位置和频率
    dependencies = []
    for r in retracted_dois:
        occurrences = find_citation_occurrences(r["doi"], paper_text)
        is_core_claim = check_if_supports_core_claim(r["doi"], paper_text)
        dependencies.append({
            "doi": r["doi"],
            "occurrence_count": len(occurrences),
            "sections": [o["section"] for o in occurrences],
            "supports_core_claim": is_core_claim,
            "severity": "critical" if is_core_claim else "moderate",
        })
    
    has_critical = any(d["severity"] == "critical" for d in dependencies)
    return {
        "has_retracted": True,
        "retracted_count": len(retracted_dois),
        "dependencies": dependencies,
        "action_required": "replace_evidence" if has_critical else "add_caveat",
    }
```

## 输出格式
撤稿检查报告（写入 `outputs/lit/<project>-retraction-check.md`）:
- **检查总数 / 撤稿数 / 关注数 / 更正数** 统计
- **撤稿论文清单**:每条含 DOI、撤稿原因、撤稿日期
- **依赖性评估**:核心论点是否依赖撤稿论文
- **建议动作**:替换证据 / 添加注意事项 / 无需处理

## 约束
- 三源交叉验证，单源判定不算最终结论
- 撤稿论文支持核心 claim 时必须标记 critical，不得放行
- Retraction Watch 数据库可能延迟，Crossref 为权威源
- 检查结果必须记录到 research-integrity-gates 的 scoring_trajectory
- 依赖性评估必须人工确认，不得自动替换引用

## 与现有 skill 的关系
- **与 citation-verification 互补**:citation-verification 验证存在性，retraction-check 验证撤稿状态
- **与 research-integrity-gates 协同**:retracted_source_dependency 门控的数据源
- **与 paper-qa-rag 协同**:paper-qa-rag 内置轻量撤稿检查，retraction-check 是专项深度检查
- **与 claim-verification 协同**:retraction-check 评估依赖性时调用 claim-verification

## 依赖工具/API
- Crossref API（撤稿标记检查）
- Retraction Watch Database
- Semantic Scholar API（论文状态）

## 关键方法论引用
- PaperQA2 retraction check: https://github.com/Future-House/paper-qa
- Retraction Watch Database: https://retractionwatch.com
- Crossref update-to 机制: https://api.crossref.org/works
