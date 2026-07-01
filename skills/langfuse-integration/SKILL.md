# langfuse-integration — 可观测性导出集成

## 用途
将 Loop 工程的全链路 trace（root_span → node_span → child_span）导出到 Langfuse 自托管实例，提供可视化 trace 树、成本/token/latency 监控、Prompt 版本管理、Evals 评估面板。与 `observability.policy.json` 协同，是可观测性策略的导出后端实现。

适用于:生产环境部署后需要全链路监控、成本归因、Prompt A/B 测试、质量回归检测的场景。

## 触发条件
- 环境变量 `OBSERVABILITY_EXPORTER=langfuse` 已设置
- 用户要求"接入 Langfuse""导出 trace""配置可观测性"
- 生产部署前的可观测性就绪检查
- cost-control 策略触发 critical 告警需要可视化排查

## 操作步骤

### 步骤 1:部署 Langfuse 自托管实例
```bash
# Docker Compose 一键部署
git clone https://github.com/langfuse/langfuse.git
cd langfuse
docker compose up -d

# 默认地址 http://localhost:3000
# 首次访问创建组织 → 项目 → 获取 API Keys
```

### 步骤 2:配置环境变量
```bash
# 写入 agent-system/.env
OBSERVABILITY_EXPORTER=langfuse
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxx
```

### 步骤 3:trace 导出适配器
```python
import os
from langfuse import Langfuse

langfuse = Langfuse(
    host=os.environ["LANGFUSE_HOST"],
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
)

def export_loop_trace(run_id: str, traces_file: str):
    """将 agent-system/runs/<run_id>/traces.jsonl 导出到 Langfuse"""
    with open(traces_file, encoding="utf-8") as f:
        for line in f:
            span = json.loads(line)
            _create_langfuse_span(span, parent_map={})

def _create_langfuse_span(span: dict, parent_map: dict):
    span_type = span.get("type", "unknown")
    if span_type == "loop_run":
        trace = langfuse.trace(
            id=span["run_id"],
            name=f"loop_run:{span.get('context_id','')}",
            user_id=span.get("user_intent_hash"),
        )
        parent_map[span["run_id"]] = trace
    elif span_type in ("context", "decide", "act", "evaluate"):
        parent = parent_map.get(span.get("run_id"))
        if parent:
            node = parent.span(
                name=f"node:{span_type}",
                metadata=span,
            )
            parent_map[span["span_id"]] = node
    elif span_type in ("llm_call", "tool_call", "agent_handoff"):
        parent = parent_map.get(span.get("parent_span_id"))
        if parent:
            child = parent.span(
                name=f"child:{span_type}",
                metadata=span,
                input=span.get("input_hash"),
                output=span.get("output_hash"),
            )
            if span_type == "llm_call":
                child.generation(
                    model=span.get("model"),
                    usage={
                        "prompt_tokens": span.get("prompt_tokens", 0),
                        "completion_tokens": span.get("completion_tokens", 0),
                    },
                )
```

### 步骤 4:Prompt 版本管理同步
```python
def sync_prompt_to_langfuse(prompt_id: str, version: str, prompt_text: str, model: str):
    """将 agent-system/prompts/<prompt_id>/<version>.json 同步到 Langfuse"""
    langfuse.create_prompt(
        name=prompt_id,
        prompt=prompt_text,
        config={"model": model, "version": version},
    )
```

### 步骤 5:验证导出
```bash
# 触发一次测试 run
python agent-system/bin/office-system.py --task "test observability"

# 在 Langfuse UI 查看 trace 树
# http://localhost:3000 → Traces → 搜索 run_id
```

## 输出格式
- Langfuse UI 中的 trace 树（root → node → child 三层）
- 成本归因面板（按 run/agent/skill/model 分解）
- Prompt 版本历史与 A/B 测试结果
- Evals 面板（评分轨迹、失败类分布）

## 约束
- 导出异步执行，不得阻塞 Loop 主流程
- trace 中 PII 必须脱敏（与 observability.policy.json retention.pii_redaction 对齐）
- Langfuse 不可用时降级为本地 jsonl（不中断服务）
- Prompt 同步必须保留版本链（parent_version → child_version）

## 依赖工具/API
- Langfuse Python SDK: `pip install langfuse`
- Docker（自托管部署）
- 环境变量: LANGFUSE_HOST / LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY

## 关键方法论引用
- Langfuse Tracing 设计: https://github.com/langfuse/langfuse
- OpenTelemetry GenAI semantic conventions: https://opentelemetry.io/docs/specs/semconv/gen-ai/
- observability.policy.json: agent-system/observability.policy.json
