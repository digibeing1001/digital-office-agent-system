# claim-verification — claim 验证

## 用途
逐条 claim 验证(SciFact 范式):提取论文中的科学声明,检索相关文献,对比判定每条 claim 是否被已有文献支持或反驳。用于论文评审、文献综述中的声明核查。

## 触发条件
- 需要验证论文中某条科学声明是否有文献支撑时。
- 论文评审时核查作者 claim 时。
- 用户提到"claim 验证""SciFact""声明核查"时。

## 工具依赖
无额外依赖,使用 API 检索:
```bash
pip install requests
# 可选:接入 Semantic Scholar / PubMed API 做文献检索
```

## 操作步骤
1. 从待验证文本中提取 claim(方法声明、性能声明、因果声明)。
2. 对每个 claim 构造检索查询(关键词 + 同义词)。
3. 检索相关文献(S2 API / PubMed / 本地知识库)。
4. 逐条对比:claim 与检索到的文献是否一致。
5. 判定:SUPPORT(文献支持)/ REFUTE(文献反驳)/ NOT_ENOUGH_EVIDENCE(无相关文献)。
6. 附证据文献。

## 调用示例
```python
import requests

def retrieve_evidence(claim, top_k=5):
    """用 Semantic Scholar API 检索相关文献"""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": claim,
        "limit": top_k,
        "fields": "title,abstract,year,externalIds"
    }
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code == 200:
        return resp.json().get("data", [])
    return []

def verify_claim(claim):
    """验证单个 claim"""
    evidence = retrieve_evidence(claim)
    print(f"\nclaim: {claim}")
    print(f"检索到 {len(evidence)} 篇相关文献:")
    for i, paper in enumerate(evidence):
        title = paper.get("title", "N/A")
        year = paper.get("year", "N/A")
        print(f"  [{i+1}] {title} ({year})")

    # 此处接入 LLM 判定 SUPPORT/REFUTE/NOT_ENOUGH_EVIDENCE
    # 输入:claim + evidence abstracts → 输出:判定 + 理由
    if len(evidence) == 0:
        return {"claim": claim, "verdict": "NOT_ENOUGH_EVIDENCE", "evidence": []}
    # 实际应用中用 LLM 对比 claim 与 evidence
    return {"claim": claim, "verdict": "待LLM判定", "evidence": evidence}

claims = [
    "Transformer 架构在机器翻译任务上优于 RNN。",
    "BatchNorm 在小 batch size 下性能下降。",
]

for claim in claims:
    result = verify_claim(claim)
    print(f"判定: {result['verdict']}")
```

## 输出格式
- 逐 claim 验证报告:claim 文本、判定(SUPPORT/REFUTE/NOT_ENOUGH_EVIDENCE)、证据文献列表。
- 汇总:支持率、反驳率、未验证率。

## 约束
- 每个 claim 独立验证,不可合并多条 claim 一起判。
- 判定必须附证据文献,不可凭空判定。
- NOT_ENOUGH_EVIDENCE 不等于 REFUTE,不可混淆。
- 检索查询语句需记录,保证可复现。
