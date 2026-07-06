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

## 已落实的可扩展 Skill（10 个新 skill）

基于调研结果，已将 6 个可扩展方向落实为 10 个内置 skill，避免与现有 40+ skill 重复：

| 新 Skill | 补强方向 | 参考来源 | 核心能力 | 与现有 skill 的关系 |
|---|---|---|---|---|
| `langfuse-integration` | 可观测性导出 | Langfuse | 全链路 trace 导出 + Prompt 版本同步 + A/B 测试 | 与 observability.policy.json 协同 |
| `paper-qa-rag` | 科学文献 RAG | PaperQA2 | 文献问答 + 撤稿检查 + 矛盾检测 + 元数据增强 | 与 arxiv-search 互补（检索 vs 问答） |
| `deep-research` | 树状递归深度研究 | gpt-researcher | 问题树 + 并行执行 + 多源检索 + 综合去重 | 与 arxiv-search/paper-qa-rag 协同 |
| `verification-loops` | 多样本投票验证 | ECC | 3 样本独立采样 + 解耦 judge + 多数表决 + 分歧检测 | 与 quality-scoring final_delivery 协同 |
| `goap-planner` | GOAP A* 目标规划 | Ruflo | 状态空间搜索 + 动作库 + 最短路径 + 失败重规划 | 与 ai-native-loop Decide 节点协同 |
| `reflexion-loop` | 4 策略反思循环 | 错误反思机制 | NONE/LAST_ATTEMPT/REFLEXION/组合 + 情景记忆 | 与 experience-extraction 互补（任务级 vs 项目级） |
| `storm-survey` | 综述生成 | STORM | 视角引导提问 + 模拟对话 + 大纲 + 全文写作 | 与 academic-writing 协同 |
| `retraction-check` | 撤稿专项检查 | PaperQA2 + Retraction Watch | 三源交叉检查 + 依赖性评估 | 与 citation-verification 互补 |
| `cross-model-verification` | 跨模型交叉验证 | academic-research-skills | 不同家族模型评分 + 一致性计算 + 第三方仲裁 | 与 verification-loops 互补（跨模型 vs 同模型） |
| `socratic-elicitation` | Socratic 引导立项 | academic-research-skills | 意图探测 + Socratic 问题 + 对话引导 + 立项摘要 | 与 ai-native-loop context 节点协同 |

### Skill 与角色的映射

| 角色 | 新增可用 Skill |
|---|---|
| 科研秘书 (secretary) | socratic-elicitation, goap-planner, langfuse-integration |
| 课题规划师 (pi) | socratic-elicitation, goap-planner, deep-research |
| 文献研究员 (literature-researcher) | deep-research, paper-qa-rag, storm-survey, retraction-check |
| 学术写作员 (academic-writer) | storm-survey, reflexion-loop |
| 方法学专家 (methodologist) | goap-planner, reflexion-loop |
| 实现工程师 (research-engineer) | goap-planner, reflexion-loop |
| 数据分析师 (data-analyst) | reflexion-loop |
| 质检员 (peer-reviewer) | verification-loops, cross-model-verification, retraction-check |
| 伦理员 (ethics) | retraction-check |
| 资料员 (knowledge-curator) | paper-qa-rag, deep-research |

### 候选源注册

同时在 `skills.sources.json` 的 `candidate_sources` 中新增 9 个 GitHub 候选源，标记为 `research_only_stage_before_install` 或 `research_only_reference`，未来可按需走 `check_stage_verify_approve` 流程安装：

- academic-research-skills (Imbad0202)
- gpt-researcher (assafelovic)
- paper-qa (Future-House)
- Langfuse
- ruflo (ruvnet)
- ECC (affaan-m)
- storm (stanford-oval)
- OpenHive (aden-hive)
- 错误反思机制（自研实现）

## 后续可扩展方向（未落实，待评估）

1. **安装 academic-research-skills 插件**：`/plugin marketplace add Imbad0202/academic-research-skills`，其 13+12+7+10 四套 Agent 团队可作为现有角色的能力增强（已作为候选源注册）
2. **安装 gpt-researcher skill**：`npx skills add assafelovic/gpt-researcher`（已作为候选源注册）
3. **引入 ECC 的 selective install**：loop/quality-gate/state-store/nanoclaw 四个组件（已作为候选源注册）
4. **引入 Ruflo 的 GOAP 规划器原版**：已将理念落实为 skills/goap-planner，可考虑安装原版插件获得更多能力
