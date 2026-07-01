# entity-extraction — 实体抽取

## 用途
从论文集中抽取共享的底层概念(方法名、数据集名、指标名、任务类型),去重归一后存入实体库,形成跨论文的知识图谱,支持方法对比和综述。

## 触发条件
- 需要从论文集中抽取方法/数据集/指标等实体时。
- 构建领域知识图谱时。
- 用户提到"实体抽取""方法对比""知识图谱"时。

## 工具依赖
无额外依赖(使用 LLM):
```bash
# 依赖项目中的 LLM 客户端
```

## 操作步骤
1. 输入论文集(标题+摘要 或 全文)。
2. 用 LLM 从每篇论文抽取实体,分类:方法名、数据集名、指标名、任务类型。
3. 实体去重归一(如 "BERT" 和 "bert" 合并)。
4. 存入实体库,关联到来源论文。
5. 人工确认后入库(实体需人工确认)。

## 调用示例

Prompt 模板:
```text
你是一个学术实体抽取助手。从以下论文摘要中抽取实体,分为四类:
1. method:方法名/模型名(如 BERT, Transformer, ResNet)
2. dataset:数据集名(如 ImageNet, GLUE, SQuAD)
3. metric:评估指标名(如 accuracy, F1, BLEU)
4. task:任务类型(如 机器翻译, 图像分类, 问答)

论文标题: {title}
论文摘要: {abstract}

请以 JSON 数组输出,每个实体含:
- name: 实体名(归一化形式,首字母大写)
- type: method / dataset / metric / task
- context: 在摘要中的上下文片段

示例输出:
[
  {"name": "BERT", "type": "method", "context": "We fine-tune BERT on..."},
  {"name": "GLUE", "type": "dataset", "context": "...evaluated on GLUE benchmark"}
]
```

```python
import json

def extract_entities(title, abstract, llm_client):
    """用 LLM 抽取实体"""
    prompt = f"""你是一个学术实体抽取助手。从以下论文摘要中抽取实体,分为四类:
1. method:方法名/模型名
2. dataset:数据集名
3. metric:评估指标名
4. task:任务类型

论文标题: {title}
论文摘要: {abstract}

请以 JSON 数组输出,每个实体含 name, type, context。"""
    response = llm_client.complete(prompt)
    try:
        entities = json.loads(response)
        return entities
    except json.JSONDecodeError:
        return []

def normalize_entity(name):
    """实体归一化"""
    return name.strip().upper()  # 简化:统一大写

def build_entity_db(papers, llm_client):
    """从论文集构建实体库"""
    entity_db = {}  # {normalized_name: {type, mentions: [{paper_id, context}]}}
    for paper in papers:
        entities = extract_entities(paper["title"], paper["abstract"], llm_client)
        for e in entities:
            norm = normalize_entity(e["name"])
            if norm not in entity_db:
                entity_db[norm] = {"name": e["name"], "type": e["type"], "mentions": []}
            entity_db[norm]["mentions"].append({
                "paper_id": paper["id"],
                "context": e.get("context", "")
            })
    return entity_db

# 统计
papers = [{"id": "p1", "title": "...", "abstract": "..."}]
# db = build_entity_db(papers, llm_client)
# for name, info in sorted(db.items(), key=lambda x: len(x[1]["mentions"]), reverse=True):
#     print(f"{info['type']:8s} {name:20s} 出现{len(info['mentions'])}次")
```

## 输出格式
- 实体库 JSON:每个实体含 name、type、mentions(来源论文+上下文)。
- 统计:按类型分组、按出现频次排序。

## 约束
- 抽取的实体需人工确认后才能正式入库。
- 实体归一化要合并大小写、缩写差异(如 "bert"→"BERT")。
- 同名不同义实体(如 "Transformer" 既可能是方法也可能是架构)需人工消歧。
