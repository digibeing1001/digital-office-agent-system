# supervisor-orchestration — Supervisor 编排

## 用途
秘书作为 Supervisor 角色自动分派任务。维护角色能力注册表,按任务需求匹配最合适的角色,分派时附带上下文摘要(非全量传话),监控任务执行状态。

## 触发条件
- 用户提出需要多角色协作的复杂任务时。
- 需要把任务分派给特定角色(实现工程师/方法学专家/数据分析师等)时。
- 用户提到"分派""编排""Supervisor""调度"时。

## 工具依赖
无额外依赖。

## 操作步骤
1. 维护角色能力注册表(`capability_registry.yaml`)。
2. 接收任务,分析任务类型和所需能力。
3. 按能力匹配最合适的角色。
4. 分派任务时附带上下文摘要(而非全量原文传话)。
5. 监控任务状态(pending/running/done/failed)。
6. 汇总各角色产出。

## 调用示例

`capability_registry.yaml`:
```yaml
roles:
  implementation_engineer:
    capabilities:
      - mlflow-tracking
      - optuna-hpo
      - hydra-config
      - rl-benchmark
      - reproducibility-export
      - failure-archiving
    handles: ["训练", "实验", "调参", "RL", "复现包"]
  methodology_expert:
    capabilities:
      - doe-templates
      - causal-inference
      - power-analysis
    handles: ["实验设计", "因果", "样本量", "DOE"]
  data_analyst:
    capabilities:
      - publication-plotting
      - reproduction-verification
    handles: ["画图", "复现核对", "配图"]
  qa_inspector:
    capabilities:
      - fact-check
      - claim-verification
      - image-integrity-check
    handles: ["核查", "验证", "claim", "图片检查"]
  librarian:
    capabilities:
      - rss-aggregation
      - ocr-pipeline
      - metadata-extraction
      - dedup-engine
      - citation-network
      - entity-extraction
    handles: ["检索", "RSS", "OCR", "去重", "元数据", "引文网络"]
  ethics_officer:
    capabilities:
      - code-plagiarism-check
      - text-plagiarism-check
      - ai-content-detection
      - image-forensics
    handles: ["查重", "抄袭", "AI检测", "取证"]
```

```python
import yaml

def load_registry(path="capability_registry.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)["roles"]

def match_role(task_description, registry):
    """按任务描述匹配角色"""
    task_lower = task_description.lower()
    best_role = None
    best_score = 0
    for role, info in registry.items():
        score = sum(1 for kw in info["handles"] if kw in task_lower)
        if score > best_score:
            best_score = score
            best_role = role
    return best_role, best_score

def summarize_context(full_context, max_words=200):
    """生成上下文摘要(非全量传话)"""
    words = full_context.split()
    if len(words) <= max_words:
        return full_context
    return " ".join(words[:max_words]) + "...[截断]"

def dispatch(task, full_context, registry):
    """分派任务"""
    role, score = match_role(task, registry)
    if not role:
        return {"status": "no_match", "message": "无匹配角色"}
    summary = summarize_context(full_context)
    dispatch_msg = {
        "to": role,
        "task": task,
        "context_summary": summary,
        "capabilities": registry[role]["capabilities"],
    }
    print(f"分派 → {role} (匹配度 {score})")
    print(f"任务: {task}")
    print(f"摘要: {summary[:100]}...")
    return dispatch_msg

# 执行
registry = load_registry()
dispatch("帮我做超参调优并记录到MLflow",
         "用户在做一个图像分类项目,数据集是CIFAR-100,模型是ResNet-50...",
         registry)
```

## 输出格式
- 分派记录:目标角色、任务、上下文摘要。
- 任务状态追踪(pending → running → done/failed)。

## 约束
- 分派附带上下文摘要,非全量传话,避免上下文膨胀。
- 按能力匹配,不可随意分派给不相关角色。
- 一个任务可分派给多个角色(协作),但需明确主从。
