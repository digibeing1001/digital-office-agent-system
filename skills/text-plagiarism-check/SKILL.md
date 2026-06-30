# text-plagiarism-check — 文本查重

## 用途
对文本类产出(论文、报告、文档)做查重。使用 MinHash + LSH 近似相似度比对,与知识库中已入库文献对比,重点看核心内容(方法、数据、结论)是否实质性重复,而非只看比例。

## 触发条件
- 文本类产出提交前需要查重时。
- 怀疑文本存在抄袭/洗稿时。
- 用户提到"文本查重""查重""MinHash""相似度"时。

## 工具依赖
```bash
pip install datasketch
```

## 操作步骤
1. 对待查文本分词、去停用词,生成 shingle(n-gram)集合。
2. 用 MinHash 对 shingle 集合生成指纹签名。
3. 与知识库中已入库文献的 MinHash 指纹做 LSH 近似查询。
4. 输出相似度排序,重点看 Top-K 相似文献。
5. 人工复核高相似度文献的核心内容是否实质性重复。

## 调用示例
```python
from datasketch import MinHash, MinHashLSH
import re

def shingle(text, k=5):
    """生成 k-shingle 集合"""
    text = re.sub(r'\s+', ' ', text.lower().strip())
    words = text.split()
    return set(" ".join(words[i:i+k]) for i in range(len(words) - k + 1))

def make_minhash(text, num_perm=128):
    """生成 MinHash 签名"""
    m = MinHash(num_perm=num_perm)
    for s in shingle(text):
        m.update(s.encode("utf-8"))
    return m

# 已入库文献(知识库)
corpus = {
    "paper_001": "We propose a transformer based architecture for machine translation...",
    "paper_002": "This paper presents a novel method for image segmentation using U-Net...",
}

# 建 LSH 索引
lsh = MinHashLSH(threshold=0.3, num_perm=128)
for doc_id, text in corpus.items():
    lsh.insert(doc_id, make_minhash(text))

# 待查文本
query_text = "Our work proposes a transformer architecture for neural machine translation tasks."
query_mh = make_minhash(query_text)

# 查询相似文献
result = lsh.query(query_mh)
print(f"相似文献: {result}")

# 计算精确 Jaccard 相似度
for doc_id in result:
    sim = query_mh.jaccard(make_minhash(corpus[doc_id]))
    print(f"  {doc_id}: Jaccard={sim:.3f}")
    if sim > 0.5:
        print(f"  ⚠️ 核心内容可能存在实质性重复,需人工核查")
```

## 输出格式
- 相似文献列表(按相似度排序),含 Jaccard 相似度。
- 高相似度(>阈值)文献标红,提示人工复核。

## 约束
- 查重看实质不看比例:核心内容(方法/数据/结论)重复才是问题,套话/通用表述重复不算。
- 阈值需合理设置(默认 0.3 触发复核,0.5 标红)。
- MinHash 为近似算法,高相似度结果需人工确认。
- 知识库需持续更新,否则漏报。
