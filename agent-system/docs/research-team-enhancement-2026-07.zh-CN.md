# 科研团队能力补强（2026-07-01）

> 基于 getnote 笔记库已有知识 + GitHub 调研结果的补强落实。不破坏现有架构，新增四个策略文件和一个状态查询命令。

## 为什么补强

现有 research-team 分支已有完整的 Loop 工程（Context-Decide-Act-Evaluate 四节点 + 确定性控制器）、10 个科研角色、94 个技能、六维评分卡、反思进化闭环。但调研发现三个缺失：

1. **可控性/透明度不足** — 缺少全链路 Tracing、评分轨迹跟踪、可观测性策略
2. **Token 成本居高不下** — 缺少四层预算、模型路由、熔断器、限流
3. **AI 科研失效模式防护不足** — 缺少幻觉引用、方法伪造、数据伪造等硬性门控

## 补强来源

基于 getnote 笔记库中已有的 Loop Engineering 和多 Agent 协同知识作为上下文，到 GitHub 调研 30+ 项目，筛选出以下参考：

| 补强方向 | 参考项目 | 借鉴点 |
|---|---|---|
| 可观测性 | [Langfuse](https://github.com/langfuse/langfuse) | 全链路 Tracing、Metrics、Evals、Prompt Management |
| 成本控制 | [OpenHive](https://github.com/aden-hive/hive) | 三态熔断器、滑动窗口限速、Token 桶 |
| 模型路由 | ECC cost-aware-llm-pipeline | 按复杂度路由模型 |
| 科研完整性 | [academic-research-skills](https://github.com/Imbad0202/academic-research-skills) | 7-mode 完整性门控、评分轨迹跟踪、跨模型验证 |
| 状态查询 | [ECC](https://github.com/affaan-m/ECC) | `ecc status` 单命令查看 readiness/sessions/health |
| 撤稿检查 | [PaperQA2](https://github.com/Future-House/paper-qa) | 自动获取论文元数据 + 撤稿标记 |
| 引用验证 | Semantic Scholar API | 每条引用验证存在性 |

## 新增文件

### 1. `agent-system/observability.policy.json` — 可观测性策略

参考 Langfuse 设计，为 Loop 工程的每个节点、每次 Agent 调用、每次工具调用提供可追溯的执行视图。

**核心内容**：
- **Trace 模型**：root_span（loop_run）→ node_span（context/decide/act/evaluate）→ child_span（llm_call/tool_call/agent_handoff）
- **Metrics**：per_run（cycles/cost/rework）、per_agent（tasks/score/duration）、per_skill（invocation/success/latency）、system_health
- **Eval hooks**：stage gate 评分记录、final delivery 多样本投票
- **Prompt Management**：版本化、A/B 测试、回滚
- **Export**：原生 jsonl + Langfuse 兼容 + OpenTelemetry 兼容
- **保留期**：traces 90 天、metrics 365 天、聚合 2555 天、PII 自动脱敏

### 2. `agent-system/cost-control.policy.json` — 成本控制策略

参考 OpenHive 三态熔断器和 ECC cost-tracking 设计。

**核心内容**：
- **四层预算**：run_level（单次 5M micro-units）、agent_level（单 Agent 1M）、daily_level（每日 50M / 100 runs）、monthly_level（每月 1B）
- **模型路由**：trivial→cheap、moderate→standard、complex→strong、critical→strong+judge解耦
- **三态熔断器**：closed（正常）→ open（快速失败）→ half_open（探测恢复），scoped to tool/model/agent/skill
- **限流**：Token 桶（容量 100，补充 60/分钟）+ 滑动窗口（60 秒 30 请求）+ 并发限制（3 runs / 3 agents per run）
- **告警**：70% warning、90% critical、3 次 rework critical
- **成本记录**：jsonl 格式，按 run/agent/skill/model/day/month 聚合

### 3. `agent-system/research-integrity-gates.policy.json` — 科研完整性门控

参考 academic-research-skills 的 7-mode 完整性阻断清单，针对 AI 科研失效模式设计硬性门控。

**7 个门控模式**：

| 门控 | 触发角色 | 检查内容 | 失败动作 |
|---|---|---|---|
| 幻觉引用阻断 | 写作员/文献员/PI | 每条引用通过 Semantic Scholar 验证 | replan，最多 2 次 |
| 方法伪造阻断 | 方法学/工程师 | 方法步骤可追溯到脚本或文献 | replan，最多 2 次 |
| 框架锁定阻断 | PI/方法学 | 框架与近 2 年工作相似度 < 0.8 | replan，最多 2 次 |
| 数据伪造阻断 | 数据师/工程师 | 数字可追溯到原始数据+脚本 | **直接 fail**，不可返工 |
| 过度泛化阻断 | 写作员/PI | claim 限定词与实验范围匹配 | replan，最多 2 次 |
| 撤稿来源阻断 | 文献员/PI/写作员 | 核心论点不依赖撤稿论文 | replan，最多 2 次 |
| 可复现性缺口阻断 | 工程师/方法学 | 附带可复现包（代码+数据+配置+种子+环境） | replan，最多 2 次 |

**附加能力**：
- 评分轨迹跟踪（趋势/波动/停滞/回退检测）
- 跨模型验证（关键产出用不同模型家族交叉验证，agreement ≥ 0.8）
- 与 quality-scoring.policy.json 的 hard_disqualifier 映射

### 4. `agent-system/bin/loop-status.py` — Loop 状态查询命令

参考 ECC 的 `ecc status` 命令设计。

**用法**：
```bash
# 查看指定 run 状态
python agent-system/bin/loop-status.py --run-id <run_id>

# 输出 markdown 格式（适合写入 status.md）
python agent-system/bin/loop-status.py --run-id <run_id> --markdown

# CI 门控（不就绪时返回非零退出码）
python agent-system/bin/loop-status.py --run-id <run_id> --exit-code
```

**输出内容**：
- run readiness（是否就绪继续）
- status / current_node / controller_decision / cycles
- cost（total / budget / remaining / utilization）
- score trend（trend / last_score / volatility）
- integrity gates（triggered / blocked）
- readiness issues（预算告警 / 评分退化 / 门控阻断）

## 修改文件

### `agent-system/coordination.policy.json` — 增强协同策略

在现有 drift_controls 之后新增四个 section：

- **cost_controls**：引用 cost-control.policy.json，约束 max_parallel_agents 与并发限制取较小值
- **observability_controls**：引用 observability.policy.json，要求每次交接和节点跳转都记录 trace
- **integrity_controls**：引用 research-integrity-gates.policy.json，门控失败时阻断 complete 决策
- **enhancement_version**：标记为 2026-07-01 补强

## 与现有架构的关系

```
现有架构（不修改）                    新增补强
┌─────────────────────────┐         ┌──────────────────────────┐
│ ai-native-loop.manifest │◄────────│ observability.policy     │ 全链路 Tracing
│ (Context-Decide-Act-    │         │                          │ Metrics + Evals
│  Evaluate + 控制器)      │◄────────│ cost-control.policy      │ 四层预算 + 熔断器
│                         │         │                          │ 模型路由 + 限流
│ quality-scoring.policy  │◄────────│ research-integrity-gates │ 7-mode 完整性门控
│ (7点评分 + failure_class)│         │                          │ 评分轨迹 + 跨模型
│                         │         │                          │
│ coordination.policy     │◄────────│ cost/observability/      │ 引用新策略
│ (5种协同模式)            │         │ integrity controls       │ 增强约束
│                         │         │                          │
│ 10角色 + 94技能         │◄────────│ bin/loop-status.py       │ 状态查询命令
└─────────────────────────┘         └──────────────────────────┘
```

**关键原则**：
- 不修改 ai-native-loop.manifest.json（Loop 核心架构不变）
- 不修改 quality-scoring.policy.json（评分卡不变，integrity-gates 是其科研场景特化层）
- 不修改现有角色和技能（只在 evaluate 节点后增加 integrity gate 检查）
- 新策略通过 coordination.policy.json 的引用接入，可独立启停

## 验证清单

- [ ] `observability.policy.json` 的 trace_model 与 ai-native-loop.manifest.json 的 stages 字段对齐
- [ ] `cost-control.policy.json` 的 run_level limits 与 controller.default_budgets 对齐
- [ ] `research-integrity-gates.policy.json` 的 applies_to_roles 与现有 10 个角色名匹配
- [ ] `coordination.policy.json` 的 cost_controls.max_parallel_agents_with_cost_awareness 不与现有 max_parallel_agents=3 冲突
- [ ] `loop-status.py` 依赖的文件路径与 state_model.storage 一致
- [ ] 所有 JSON 文件格式合法
- [ ] 所有策略文件有 version 和 kind 字段，遵循现有约定

## 后续可扩展方向

1. **接入 Langfuse 自托管**：设置 `OBSERVABILITY_EXPORTER=langfuse` 环境变量即可导出 trace 到 Langfuse
2. **接入 PaperQA2 作为知识库后端**：增强资料员和文献研究员的 RAG 能力
3. **安装 academic-research-skills 插件**：`/plugin marketplace add Imbad0202/academic-research-skills`，其 13+12+7+10 四套 Agent 团队可作为现有角色的能力增强
4. **安装 gpt-researcher skill**：`npx skills add assafelovic/gpt-researcher`，增强深度研究能力
5. **引入 ECC 的 Verification Loops**：selective install loop/quality-gate/state-store/nanoclaw 四个组件
6. **引入 Ruflo 的 GOAP 规划器**：增强 Decide 节点的规划能力
