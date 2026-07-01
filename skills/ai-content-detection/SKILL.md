# ai-content-detection — AI 生成内容检测

## 用途
检测文本是否由 AI(大语言模型)生成。综合困惑度、词汇多样性、DetectGPT 扰动检测等多维度指标,多模型投票,输出参考性判断。明确标注"参考性指标,非定论"。

## 触发条件
- 需要检测文本是否 AI 生成时。
- 学术诚信审查时。
- 用户提到"AI 检测""AI 生成""DetectGPT""GPT 检测"时。

## 工具依赖
无额外依赖(多模型投票自实现):
```bash
pip install transformers torch numpy
```

## 操作步骤
1. 算困惑度(perplexity):AI 文本通常困惑度偏低。
2. 算词汇多样性(type-token ratio / burstiness):AI 文本词汇多样性偏低。
3. DetectGPT 思路:对文本做小幅扰动,看原文本概率是否显著高于扰动版本。
4. 多维度指标投票,综合判定。
5. 标注"参考性指标,非定论,不单独作为判定依据"。

## 调用示例
```python
import math
import numpy as np
from collections import Counter
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

tokenizer = AutoTokenizer.from_pretrained("gpt2")
model = AutoModelForCausalLM.from_pretrained("gpt2")
model.eval()

def calc_perplexity(text):
    """计算困惑度,AI 文本通常困惑度低"""
    enc = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**enc, labels=enc["input_ids"])
    return math.exp(outputs.loss.item())

def calc_burstiness(text):
    """词汇多样性(burstiness),AI 文本通常偏低"""
    words = text.split()
    freq = Counter(words)
    counts = np.array(list(freq.values()))
    return float(counts.std() / counts.mean()) if counts.mean() > 0 else 0

def detectgpt_score(text, n_perturb=10):
    """DetectGPT:原文本概率 vs 扰动文本概率"""
    import random
    orig_logp = -calc_perplexity(text)  # 简化:用负困惑度近似
    perturb_scores = []
    words = text.split()
    for _ in range(n_perturb):
        # 随机替换一个词(简化版)
        if len(words) < 2:
            break
        idx = random.randint(0, len(words) - 1)
        words_p = words.copy()
        words_p[idx] = "the"  # 简化替换
        perturb_scores.append(-calc_perplexity(" ".join(words_p)))
    if not perturb_scores:
        return 0.0
    return orig_logp - np.mean(perturb_scores)  # 正值越大越可能是 AI 生成

def detect_ai(text):
    ppl = calc_perplexity(text)
    burst = calc_burstiness(text)
    dgpt = detectgpt_score(text)

    votes = 0
    if ppl < 30: votes += 1         # 困惑度低
    if burst < 0.8: votes += 1      # 多样性低
    if dgpt > 0.5: votes += 1       # DetectGPT 偏高

    verdict = "疑似AI生成" if votes >= 2 else "可能人工撰写"
    print(f"困惑度: {ppl:.1f} | 多样性: {burst:.2f} | DetectGPT: {dgpt:.3f}")
    print(f"投票: {votes}/3 → {verdict}")
    print("⚠️ 参考性指标,非定论,不单独作为判定依据")

detect_ai("The transformer architecture has revolutionized natural language processing.")
```

## 输出格式
- 多维度指标:困惑度、词汇多样性、DetectGPT 分数。
- 投票结果(几项命中)。
- 参考性判断 + 风险提示。

## 约束
- 明确标注"参考性指标,非定论",不单独作为判定依据。
- 多模型/多指标投票,不可单凭困惑度下定论。
- 检测结果需人工复核,不可直接用于处罚。
- 短文本(<50 词)检测不可靠,需标注。
