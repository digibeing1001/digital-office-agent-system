# fact-check — 事实核查

## 用途
对论文/报告中的声明(claim)做原子级事实核查。把长文本拆成不可再分的 atomic claim,每个 claim 独立检索验证,判定为 SUPPORT / REFUTE / NOT_ENOUGH_EVIDENCE,并附证据来源。

## 触发条件
- 论文交稿前需要事实核查时。
- 对某段文字的可信度存疑时。
- 用户提到"事实核查""fact-check""FActScore"时。

## 工具依赖
```bash
pip install factscore
# FActScore 需要 retrieval 模型和 LLM,按其文档配置
```

## 操作步骤
1. 输入待核查文本(论文段落/摘要)。
2. 将文本拆成 atomic claim(每个 claim 是一个可独立验证的事实陈述)。
3. 对每个 claim 独立检索相关证据(知识库 / 网络)。
4. 判定:SUPPORT(有证据支持)/ REFUTE(有证据反驳)/ NOT_ENOUGH_EVIDENCE(证据不足)。
5. 附证据来源(引用链接/文献)。
6. 汇总 FActScore(支持 claim 占比)。

## 调用示例
```python
from factscore.factscorer import FactScorer

scorer = FactScorer()

# 待核查文本
passage = """
Our model achieves 98.5% accuracy on ImageNet, surpassing all prior methods.
The method was first proposed by Smith et al. in 2023.
Training takes 8 hours on a single RTX 4090.
"""

# FActScore 自动拆 claim + 检索 + 判定
result = scorer.score("ImageNet model claim", passage)

print(f"FActScore: {result['fact_score']:.3f}")
print(f"总 claim 数: {result['nclaims']}")
for claim in result["claims"]:
    print(f"\nclaim: {claim['claim']}")
    print(f"  判定: {claim['factuality']}")  # Supported / Refuted / NotEnoughInfo
    if claim.get("evidence"):
        for ev in claim["evidence"][:2]:
            print(f"  证据: {ev['text'][:80]}... (来源: {ev.get('source','')})")
```

手动拆 claim + 检索(无 FActScore 时):
```python
import re

def split_atomic_claims(text):
    # 按句号拆分,每句一个 atomic claim
    sentences = re.split(r'[。.]\s*', text)
    return [s.strip() for s in sentences if s.strip()]

claims = split_atomic_claims(passage)
for i, c in enumerate(claims):
    print(f"claim {i+1}: {c}")
    # 此处接入检索 API 验证每个 claim
```

## 输出格式
- 逐 claim 核查表:claim 文本、判定、证据来源。
- FActScore 汇总分(0~1)。

## 约束
- 无证据支持的 claim 标 NOT_ENOUGH_EVIDENCE,不可默认为 SUPPORT。
- 每个 claim 必须独立验证,不可"因为整段看起来对就放过"。
- 证据来源必须可追溯(引用链接/文献 DOI)。
- FActScore 仅作参考,不单独作为论文接收/拒绝依据。
