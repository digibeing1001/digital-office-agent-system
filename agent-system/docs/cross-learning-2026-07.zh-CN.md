# 三分支相互学习记录 · 2026-07

> 版本：v1.0 | 日期：2026-07-02 | 所属分支：main（数字办公系统）
> 关联：agent-team-qa-framework.zh-CN.md、coordination.policy.json、bin/loop-status、human-gate-actions.policy.json

## 一、背景

本仓库存在三个并列分支，各自服务不同场景，但共享同一套 Agent Team 工程底座：

| 分支 | 定位 | 设计目标 |
|---|---|---|
| **main** | 数字办公系统 | 面向企业的通用数字办公 Agent Team，覆盖产品/设计/研发/法务/写作全链路，强调协作拓扑与失效模式防御 |
| **research-team** | 科研团队 | 面向科研场景的 Agent Team，强调研究完整性门控、评分轨迹追踪与 loop 状态可观测 |
| **writer-team** | 写作团队 | 面向内容创作的 Agent Team，强调去 AI 味、读者价值验证与上下文资产沉淀 |

三分支在不背离各自设计目标的前提下相互学习设计经验。本文档记录 2026-07 这一轮相互学习在 **main 分支**的落地清单。research-team 与 writer-team 分支的对应落地不在本文档范围内，由各分支自行记录。

## 二、学习矩阵

下表列出本轮相互学习的内容流向与经验要点（6 行）：

| 来源 → 目标 | 学到的经验 |
|---|---|
| writer-team → main | 13 方法论 QA 执行准则（AI 自评偏见消除 / 原子化事实核查 / 工具增强审查 / 多轮体验扫描 / HHH / 多 Agent 辩论 / 错误反思情景记忆 / 自我奖励自我进化 / 风格指纹量化 / 专家提示身份条件生成 / 认知投降检测等）。main 分支按数字办公场景适配，落地为 `agent-team-qa-framework.zh-CN.md` 附录 C 的工程化落地表，标注每条方法论在 main 的具体落地位置（policy 文件 / 角色 / Gate）。 |
| writer-team → main | 11 类关键动作人工把关清单（对外发送 / 公开发布 / 上线部署 / 删除 / 覆盖 / 付款 / 数据导出 / 记入长期记忆 / 晋升为公司知识 / 受监管专业建议 / 最终交付）。main 分支将其结构化为独立策略文件 `human-gate-actions.policy.json`，与现有 `judgment.policy.json` 的 human_gated 模式对齐，超阈值（0.65）自动暂停请人确认。 |
| research-team → main | loop-status 单命令状态查询：research-team 用 Python 实现了 `loop-status.py`，提供 Run Readiness / Cost / Score Trend / Integrity Gates 一屏可读。main 分支的 `bin/` 多为无后缀的 bash/python 混合脚本，故用 bash 重写为 `bin/loop-status`，读取 main 自有的注册表与策略文件，输出 4 个区块。 |
| research-team → main | enhancement_version + enhancement_source 顶层标记模式：research-team 在 `coordination.policy.json` 顶部标注增强版本与来源，便于追溯每次补强的出处与时间。main 分支吸收此模式，在 `coordination.policy.json` 新增 `enhancement_version` 与 `enhancement_source` 两个字段，标记本轮 cross-learning 来源。 |
| main → writer-team / research-team | debate_council 对抗式评审拓扑 + subagent compression contract：main 分支已在 `coordination.policy.json` 落地成熟的 debate_council（多 reviewer + judge 收敛 + 异议记录）与 parallel_expert_dag 的 subagent 压缩信封（distilled_findings / evidence_refs / confidence_and_caveats）。该模式可反哺 writer-team 的多 Agent 辩论收敛（吸收 7）与 research-team 的并行专家评审。 |
| main → research-team / writer-team | 中层审查节奏（midlayer_review_cadence）+ Comprehension Debt 防御：main 分支已落地每 30m/2h 强制触发中层审查的早返机制，以及 human_gated 阶段强制人读 diff 写 ≥30 字总结的 Comprehension Debt 防御。该失效模式防御可补强 research-team 的慢循环 QA（防止 agent 团队空转）与 writer-team 的认知投降检测（防止作者判断力退化）。 |

## 三、main 分支本轮落地清单（5 项）

以下 5 项迭代全部在 main 分支 worktree 内执行，不触碰其他 worktree：

1. **本文档**（`agent-system/docs/cross-learning-2026-07.zh-CN.md`）：三分支相互学习记录，版本 v1.0。
2. **QA 框架附录 C**（`agent-system/docs/agent-team-qa-framework.zh-CN.md`）：新增 `## 附录 C：13 方法论工程化落地参考`，吸收自 writer-team qa-framework.md v1.1，按数字办公场景适配落地位置。
3. **loop-status 脚本**（`agent-system/bin/loop-status`）：bash 实现，吸收自 research-team loop-status.py，输出 Run Readiness / Cost Snapshot / Quality Scoring / Integrity Gates 四区块。
4. **coordination.policy.json 增强标记**（`agent-system/coordination.policy.json`）：新增 `enhancement_version` 与 `enhancement_source` 顶层字段，吸收自 research-team 的增强标记模式。
5. **human-gate-actions.policy.json**（`agent-system/human-gate-actions.policy.json`）：11 类关键动作人工把关策略，吸收自 writer-team orchestration.md，与 main 现有 human_gated 模式对齐。

## 四、后续待跟进事项

- [ ] writer-team / research-team 分支按各自场景落地 main 反哺的两项（debate_council + compression contract、中层审查节奏 + Comprehension Debt 防御），由各分支自行记录。
- [ ] 评估 `human-gate-actions.policy.json` 是否需要写入 `coordination.policy.json` 的 `human_gated` 模式引用，形成策略间显式引用链。
- [ ] 评估 `bin/loop-status` 是否接入 `harness-check` 的就绪断言，作为 CI 门控的一部分。
- [ ] 下一轮 cross-learning 视情况扩展学习矩阵（如 research-team 的评分轨迹追踪、writer-team 的上下文资产沉淀机制是否值得 main 进一步吸收）。

---

版本：v1.0 | 日期：2026-07-02 | 作者：cross-learning iteration（main 分支）
