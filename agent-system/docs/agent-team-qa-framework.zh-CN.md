# 数字办公室 Agent Team QA 框架

> 版本：1.0.0 | 创建：2026-07-02 | 关联：loop-engineering.zh-CN.md、quality-scoring.policy.json、coordination.policy.json
> 理论基础：吴恩达 Loop Engineering 三层框架 + Anthropic Multi-Agent Research System + 项目已有的 Context-Decide-Act-Evaluate 确定性控制器

## 一、为什么需要这份 QA 框架

吴恩达指出 Loop Engineering 不是单层概念，而是三层体系：

| 层级 | 定义 | 迭代速度 | 行业关注度 | 本项目对应 |
|---|---|---|---|---|
| 第一层 | 代码自主编写与自测 | 最快 | 最高（但最不重要） | coder + vibe-coding-eight-phase + verification-loop |
| 第二层 | 从业者从 QA 转向产品经理 | 中等 | 中等 | pm + product role_gate |
| 第三层 | 决定产品生死的慢循环 | 最慢 | 最低（但壁垒最高） | release.policy + human_gated |

**核心认知**：多数团队过度投入第一层编码循环优化，忽略更核心的第二、三层。本项目通过这份 QA 框架，确保 Agent Team 在每一层都有专门的质量守护，避免"功能正确但产品失败"。

**品味 = 上下文优势**：这是衔接第二层与第三层的核心能力。Agent Team 中，秘书（secretary）作为上下文中枢，承担"品味守护者"角色——不是替代人类品味，而是确保上下文优势被正确传递给每一个决策节点。

---

## 二、QA 框架总览

本框架覆盖三层 Loop QA + Agent Team 协作 QA，共四个维度：

```
┌─────────────────────────────────────────────────────────────┐
│                    第三层 QA：产品生死                        │
│   市场竞争力 · 长期价值 · 品牌一致性 · 用户留存预测           │
│   （慢循环，跨任务累积，决定产品长期生命力）                  │
├─────────────────────────────────────────────────────────────┤
│                    第二层 QA：产品品味                        │
│   需求洞察 · 体验优化 · 场景覆盖 · PM-as-QA · 品味传递        │
│   （中速循环，从验收转向价值创造）                            │
├─────────────────────────────────────────────────────────────┤
│                    第一层 QA：执行自测                        │
│   代码质量 · 迭代有效性 · 副作用幂等 · 回归保护 · 工具可靠     │
│   （快循环，最成熟但不过度投入）                              │
├─────────────────────────────────────────────────────────────┤
│               Agent Team 协作 QA（跨层）                      │
│   handoff 语义 · compression 有效性 · debate 收敛 · 角色边界  │
│   （贯穿所有层，确保团队协作不丢上下文）                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、第一层 QA：执行与自测循环

### 3.1 定位

这是最成熟的层，但吴恩达提醒"最不重要"。QA 目标不是追求代码完美，而是确保**迭代有效**且**不过度投入**。

### 3.2 已有机制（保留）

- `quality-scoring.policy.json` 的 implementation role_gate：tests_pass、code_quality、no_regressions
- `vibe-coding-production-harness` skill chain
- `verification-loop` skill
- stage 阈值：context=4, decide/act=5, evaluate=6

### 3.3 补强项

#### 3.3.1 迭代有效性 QA

防止"空转迭代"——agent 反复重试但无实质进展。

| 检查项 | 判定标准 | 触发动作 |
|---|---|---|
| 进度增量 | 每个 cycle 的 progress_delta >= 0.02（已有） | 低于阈值 → stagnant → wait_human |
| 重试质量 | 重试必须携带新的观察或修改后的假设 | 无新信息的重试 → 标记 transient_retryable 但限制 max_stage_retries |
| 迭代收敛 | 连续 2 个 cycle 的 score 差 < 0.5 且未通过 | 判定 correctable_replan，回 Decide 重规划 |
| 预算消耗率 | tool_calls / max_tool_calls > 0.8 且未通过 | 预警 → controller 评估 budget_exhausted 风险 |

#### 3.3.2 副作用幂等性 QA

| 检查项 | 判定标准 | 触发动作 |
|---|---|---|
| 幂等标记 | 每个副作用必须标记 idempotent / deduplicated / confirmed | 未标记 → 拒绝执行 |
| 幂等验证 | 标记为 idempotent 的操作重放后结果一致 | 不一致 → 降级为 confirmed，要求人工确认 |
| 去重验证 | 标记为 deduplicated 的操作检查是否已执行 | 已执行 → 跳过并记录 |

#### 3.3.3 回归保护 QA

| 检查项 | 判定标准 | 触发动作 |
|---|---|---|
| eval 用例覆盖 | release-critical 行为有 deterministic eval case | 缺失 → 阻止 complete |
| 回归基线 | 每次迭代后跑 eval suite | 有用例失败 → no_regressions 不通过 |
| smoke 覆盖 | 每次系统变更跑 smoke.sh | 失败 → 阻止 release |

### 3.4 第一层 QA 的"不过度"原则

- score=5（fail_with_minor_defects）时不强制完美，允许"有记录的小缺陷"进入下一阶段
- stage 阈值差异化：context 宽松（4），act 中等（5），evaluate 严格（6）
- 不为代码优雅性过度迭代——code_quality 权重 0.3，tests_pass 权重更高

---

## 四、第二层 QA：产品品味与需求定义

### 4.1 定位

这是吴恩达强调的"角色融合"层——QA 不再只是验收，而是转向**需求定义和体验优化**。Agent Team 中，pm 和 secretary 共同承担这一层的 QA 职责。

### 4.2 品味 = 上下文优势

品味不是主观审美，而是对场景上下文的深度理解优势。在 Agent Team 中：

- **secretary 是品味守护者**：作为上下文中枢，确保每个决策节点获得足够的上下文（不只是数据，而是对用户意图、约束、场景的深度理解）
- **pm 是品味执行者**：将上下文优势转化为精准的需求定义、验收标准和体验设计
- **人类是品味最终裁决者**：agent 可以建议，但"品味判断"需要人类确认（human_gated）

### 4.3 补强项

#### 4.3.1 需求洞察质量 QA

超越"验收标准是否明确"，评估"需求是否精准、是否有洞察"。

| 检查项 | 判定标准 | 触发动作 |
|---|---|---|
| 第一性原理问题 | 秘书至少提出 3 道第一性原理问题（已有） | 缺失 → 阻止 dispatch |
| 隐含需求挖掘 | pm 是否识别了用户未明说但关键的需求 | 缺失 → replan，要求 pm 补充 |
| 需求矛盾检测 | 需求之间是否存在冲突或矛盾 | 发现 → wait_human，要求澄清 |
| 验收标准可测性 | 每个验收标准必须有可验证的判定方式（已有） | 不可测 → replan |

#### 4.3.2 体验优化 QA

| 检查项 | 判定标准 | 触发动作 |
|---|---|---|
| 用户旅程完整性 | 设计是否覆盖完整用户旅程，而非孤立功能 | 缺失 → design role_gate 不通过 |
| 交互一致性 | UI 元素是否遵循同心圆角原则、蓝色主色调、双软阴影（项目约束） | 违反 → 设计 QA 不通过 |
| 可访问性 | 关键路径是否满足 WCAG 基本要求 | 缺失 → 标记为 fail_with_minor_defects |
| 错误体验 | 失败场景是否有友好的用户提示 | 缺失 → 补强项，不阻塞但记录 |

#### 4.3.3 场景覆盖 QA

| 检查项 | 判定标准 | 触发动作 |
|---|---|---|
| 正向场景 | 主流程有明确的场景定义 | 缺失 → 阻止 dispatch |
| 边界场景 | 至少识别 3 个边界场景 | 缺失 → replan |
| 失败场景 | 至少识别 2 个失败场景及回滚方案 | 缺失 → 风险记录补充 |

#### 4.3.4 PM-as-QA 模式

吴恩达强调角色融合。在 Agent Team 中实现"PM-as-QA"：

- pm 在需求定义阶段就预定义验收标准（不只是事后验收）
- pm 参与 evaluate 节点，从产品价值角度评分（不只是功能正确性）
- pm 有权叫停"功能正确但价值不足"的迭代

实现方式：在 `quality-scoring.policy.json` 的 product role_gate 中新增 `value_validation`（价值验证）维度。

### 4.4 第二层 QA 门禁

第二层 QA 在以下节点触发：
- **Context 阶段结束后**：需求洞察质量 QA（秘书 + pm）
- **Decide 阶段结束后**：场景覆盖 QA（pm）
- **Act 阶段结束后**：体验优化 QA（designer + pm）
- **Evaluate 阶段**：PM-as-QA 价值评分

---

## 五、第三层 QA：产品生死与长期竞争力

### 5.1 定位

这是最慢但决定产品生死的层。吴恩达指出其"慢"属性反而构建高壁垒。QA 目标是确保产品长期方向正确，不因短期迭代偏离核心价值。

### 5.2 特征

- **跨任务累积**：不是单个任务的 QA，而是跨多个任务的累积评估
- **慢循环**：迭代周期以周/月计，不是单次 run
- **人类主导**：agent 提供数据支撑，但判断由人类做出
- **不可自动化**：这正是"品味无法被 AI 替代"的体现

### 5.3 补强项

#### 5.3.1 产品方向 QA

| 检查项 | 触发频率 | 判定标准 | 触发动作 |
|---|---|---|---|
| 核心价值偏移 | 每个重大迭代提案 | 变更是否偏离产品的核心价值主张 | 偏离 → 迭代提案需 human_gated 审批 |
| 功能膨胀检测 | 每个迭代提案 | 是否增加与核心价值无关的功能 | 膨胀 → 标记风险，要求 pm 论证必要性 |
| 简洁性守护 | 每个设计评审 | 是否能用更简单的方式达成同样目标 | 过度复杂 → debate_council 评审 |

#### 5.3.2 品牌一致性 QA

| 检查项 | 触发频率 | 判定标准 | 触发动作 |
|---|---|---|---|
| 视觉品牌 | 每次设计变更 | 是否遵循蓝色主色调、同心圆角、双软阴影 | 违反 → 设计 QA 不通过 |
| 交互品牌 | 每次交互变更 | 是否遵循一致的交互模式（hover/press/disabled） | 违反 → 标记不一致 |
| 语言品牌 | 每次文案变更 | 是否符合项目语言风格（专业、非 AI 腔） | 违反 → writer role_gate 不通过 |

#### 5.3.3 长期健康 QA

| 检查项 | 触发频率 | 判定标准 | 触发动作 |
|---|---|---|---|
| 技术债累积 | 每次发布 | eval suite 是否有新增的跳过/失败用例 | 恶化 → 阻止 release |
| 知识库质量 | 每月 | 知识条目是否有过时、重复、矛盾 | 发现 → 知识治理任务 |
| Agent 行为漂移 | 每月 | agent 决策是否符合 SOUL 定义 | 漂移 → SOUL 校准任务 |
| 用户满意度趋势 | 每季度 | 用户体验反馈是否下降 | 下降 → 产品复盘（human_gated） |

### 5.4 第三层 QA 的"慢"原则

- 不追求每个 run 都触发第三层 QA
- 第三层 QA 通过"迭代提案"机制触发（secretary.capabilities.json 已有）
- 重大变更（SOUL/Skill/工作流/规则/知识晋升/模型路由/GUI 契约/发布配置）必须走 human_gated
- 第三层 QA 的结论写入项目记忆，作为未来任务的上下文

---

## 六、Agent Team 协作 QA（跨层）

### 6.1 定位

协作 QA 贯穿所有层，确保 Agent Team 在协作过程中不丢失上下文、不产生语义断层。

### 6.2 Handoff 语义完整性 QA

已有机制：typed envelope + contract hash + checkpoint。补强语义层：

| 检查项 | 判定标准 | 触发动作 |
|---|---|---|
| 上下文无损 | handoff envelope 包含接收方所需的全部字段 | 缺失 → 接收方拒绝接收 |
| 语义对齐 | 接收方理解的意图与发送方一致 | 不一致 → wait_human |
| 产物可达性 | artifact_ref 指向的产物实际存在且可访问 | 不可达 → 阻止 complete |
| 确认闭环 | 接收方必须显式 acknowledge | 未确认 → handoff 未完成 |

### 6.3 Context Compression 有效性 QA

针对 `parallel_expert_dag` 的 subagent compression contract：

| 检查项 | 判定标准 | 触发动作 |
|---|---|---|
| 压缩保真 | distilled_findings 保留了关键结论和证据引用 | 信息丢失 → subagent 重做 |
| 无全量回放 | 主 context 未接收 full subagent trace | 违反 → 阻止 act |
| 证据可达 | evidence_refs 指向的产物存在且可访问 | 不可达 → 标记 missing_context |
| 置信度标注 | confidence_and_caveats 必须填写 | 缺失 → 压缩不通过 |

### 6.4 Debate Council 收敛质量 QA

| 检查项 | 判定标准 | 触发动作 |
|---|---|---|
| 独立性 | reviewers 使用不同 prompt 或模型 | 相同 → 降为单 reviewer，不满足 debate_council |
| 覆盖度 | reviewers 覆盖了关键风险维度 | 遗漏 → 补充 reviewer |
| 收敛判定 | 高风险需双通过；中风险多数+judge | 未收敛 → judge 介入或 wait_human |
| 异议记录 | 分歧点和各方立场已记录 | 缺失 → debate 结果无效 |

### 6.5 角色边界一致性 QA

| 检查项 | 判定标准 | 触发动作 |
|---|---|---|
| 职责不越界 | coder 不做产品决策，pm 不写代码 | 越界 → 标记 drift |
| 角色融合点 | PM-as-QA 是允许的融合点（第二层） | 合规 → 通过 |
| 交接不回退 | 已交接的工作不回退给前一个角色 | 回退 → replan |

---

## 七、QA 角色与职责矩阵

吴恩达强调"角色融合"，但融合不等于无边界。以下是 QA 职责矩阵：

| QA 维度 | 主导角色 | 协作角色 | 人类参与 |
|---|---|---|---|
| 第一层·迭代有效性 | coder | secretary | 异常时 |
| 第一层·副作用幂等 | coder | secretary | 高风险时 |
| 第一层·回归保护 | coder | secretary | 发布时 |
| 第二层·需求洞察 | pm | secretary | 必须（意图确认） |
| 第二层·体验优化 | vibe-designer | pm | 品味判断时 |
| 第二层·场景覆盖 | pm | researcher | 异常时 |
| 第二层·PM-as-QA | pm | secretary | 价值争议时 |
| 第三层·产品方向 | secretary | pm | 必须（human_gated） |
| 第三层·品牌一致 | vibe-designer | writer | 重大变更时 |
| 第三层·长期健康 | secretary | 全员 | 必须（季度复盘） |
| 协作·handoff 语义 | 接收方 | 发送方 | 异常时 |
| 协作·compression | secretary | subagents | 异常时 |
| 协作·debate 收敛 | judge | reviewers | 高风险时 |
| 协作·角色边界 | secretary | 全员 | 漂移时 |

**秘书的核心 QA 职责**：secretary 不仅是 intake，更是全流程的 QA 协调者。在每个节点结束时，secretary 负责：
1. 收集各角色的 QA 评分
2. 汇总到 evaluate 节点
3. 识别跨角色的不一致
4. 在 controller 决策时提供 QA 依据

---

## 八、QA 流程与门禁

### 8.1 QA 在 Loop 中的触发点

```
Context ──→ [QA1: 需求洞察 + 场景覆盖] ──→ Decide
Decide  ──→ [QA2: 决策质量 + 角色边界] ──→ Act
Act     ──→ [QA3: 执行质量 + 副作用 + compression] ──→ Evaluate
Evaluate──→ [QA4: 多层评分 + PM-as-QA + debate(可选)] ──→ Controller
```

### 8.2 门禁规则

| 门禁 | 触发条件 | 通过标准 | 不通过动作 |
|---|---|---|---|
| QA1 | Context 阶段结束 | 第一性原理问题 >= 3，需求无矛盾，场景覆盖 | replan 或 wait_human |
| QA2 | Decide 阶段结束 | 决策有依据，风险已记录，角色不越界 | replan |
| QA3 | Act 阶段结束 | 副作用幂等，handoff 确认，compression 有效 | retry 或 replan |
| QA4 | Evaluate 阶段 | 多层评分通过阈值，PM-as-QA 价值验证 | controller 决策 |

### 8.3 第三层 QA 的特殊触发

第三层 QA 不在每个 run 内触发，而是在以下事件触发：
- 迭代提案创建时（secretary.capabilities.json 的 iteration_report_must_include）
- 发布前（release.policy.json 的 release_flow）
- 季度复盘时（人工发起）

---

## 九、QA 度量与回归

### 9.1 QA 有效性度量

| 指标 | 定义 | 目标 |
|---|---|---|
| 首次通过率 | 一次 run 中 QA4 直接通过的比率 | > 40% |
| 平均迭代次数 | 通过 QA4 前的平均 cycle 数 | < 2.5 |
| 空转率 | progress_delta < 0.02 的 cycle 比率 | < 15% |
| handoff 拒绝率 | 接收方拒绝 handoff 的比率 | < 10% |
| 品味偏差率 | 人类在 QA4 后推翻 agent 评定的比率 | < 20% |
| 回归捕获率 | eval suite 捕获的回归数 / 实际回归数 | > 90% |

### 9.2 QA 回归测试

QA 框架本身需要回归保护：
- 每次系统变更后跑 `smoke.sh`（已有）
- QA 框架变更后跑 `evals/runtime-replay-and-multilingual.json`（已有）
- 新增：QA 度量每月统计一次，写入项目记忆

---

## 十、与现有策略的集成点

| 现有策略 | 集成方式 |
|---|---|
| `quality-scoring.policy.json` | 新增 `value_validation` 到 product role_gate；新增 `iteration_effectiveness` 到 implementation role_gate |
| `coordination.policy.json` | debate_council 已集成；content_safety_guardrails 已集成 |
| `judgment.policy.json` | 第三层 QA 的 human_gated 触发条件对齐 |
| `ai-native-loop.manifest.json` | QA1-QA4 作为各阶段的 gates 补充 |
| `secretary.capabilities.json` | secretary 的 QA 协调职责写入 stage_ownership |
| `release.policy.json` | 第三层 QA 的发布前检查对齐 release_flow |

---

## 十一、关键认知总结

1. **不要过度投入第一层**：代码质量重要，但不是产品成功的决定因素。第一层 QA 的目标是"有效且不过度"。
2. **第二层是差异化关键**：PM-as-QA 模式让 Agent Team 从"做事正确"转向"做正确的事"。品味（上下文优势）是 agent 无法自动化的能力，secretary 的上下文中枢角色是品味守护的关键。
3. **第三层是长期壁垒**：慢循环的 QA 不可省略。产品方向、品牌一致性、长期健康需要跨任务累积评估，且必须人类主导。
4. **角色融合不是角色消解**：PM-as-QA 是允许的融合点，但 coder 不做产品决策、pm 不写代码的边界不变。
5. **QA 是未来的任务参考文档**：这份框架将作为 Agent Team 执行所有未来任务时的质量基准。每次 run 都应参照本框架执行 QA1-QA4，第三层 QA 在重大事件时触发。
