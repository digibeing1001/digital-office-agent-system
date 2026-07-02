# 三分支相互学习记录 · 2026-07

## 背景

`digital-office-agent-system` 仓库下存在三个并列分支，各自承载不同的设计目标：

- **main 分支**：数字办公系统，提供通用的 Agent 编排、上下文交接、质量评分、知识空间等基础设施。
- **research-team 分支**：科研团队，在 main 基础上特化为面向学术研究场景的 Agent 体系（文献检索、实验设计、论文撰写、同行评审、科研完整性门控）。
- **writer-team 分支**：写作团队，面向新媒体内容创作的 Agent 体系（选题、素材、撰稿、审查、去 AI 味、排版）。

三分支在不背离各自设计目标的前提下，相互学习设计经验。本文档记录 2026-07 批次的相互学习矩阵与 research-team 分支的落地清单。

---

## 学习矩阵

| 来源 | 目标 | 学到的经验 |
|---|---|---|
| main | research-team | context-envelope v2.0.0 工作包交接规范：版本化、哈希校验、大文件按引用传递、省略字段显式化。research-team 据此建立科研场景特化版 context-envelope（v2.0.1-research）。 |
| main | research-team | smoke 测试体系：json_assert + must_fail 模式，覆盖 JSON 合法性、字段存在性、断言表达式、预期失败命令。research-team 据此建立科研场景 smoke 骨架。 |
| writer-team | research-team | Gate 模式：每个 Gate 必须声明「必须输出」与「通过条件」，而非仅描述检查逻辑。research-team 据此为 7 个科研完整性 gate 补充 required_outputs 与 pass_conditions。 |
| writer-team | research-team | 13 方法论工程化落地：把学术论文方法论（LLM-as-judge 偏见消除、FActScore 原子化核查、CRITIC 工具增强、Reflexion 情景记忆等）映射到具体角色与 Gate。research-team 据此建立 methodology-integration 文档。 |
| research-team | main | 科研完整性门控的 7-mode 阻断清单（幻觉引用、数据伪造、方法伪造、框架锁定、过度泛化、撤稿依赖、可复现性）可为 main 的 quality-scoring hard_disqualifiers 提供场景特化参考。 |
| research-team | writer-team | 科研场景的引用验证（Semantic Scholar API + 撤稿检查）可为 writer-team 的事实核查与引用台账提供自动化查证参考。 |

---

## research-team 分支本次落地的 5 项迭代清单

| # | 迭代项 | 落地文件 | 吸收来源 |
|---|---|---|---|
| 1 | 三分支相互学习记录文档 | `agent-system/docs/cross-learning-2026-07.zh-CN.md` | — |
| 2 | context-envelope 科研特化版（v2.0.1-research） | `agent-system/context-envelope.schema.json` | main 分支 context-envelope v2.0.0 |
| 3 | 科研完整性 gate 补充 required_outputs + pass_conditions | `agent-system/research-integrity-gates.policy.json` | writer-team Gate 模式 |
| 4 | smoke 测试骨架（json_assert + must_fail） | `agent-system/tests/smoke.sh` | main 分支 smoke.sh |
| 5 | 13 方法论工程化落地（科研场景适配版） | `agent-system/docs/methodology-integration.zh-CN.md` | writer-team qa-framework.md v1.1 |

---

## 后续待跟进事项

1. **context-envelope v2.0.1-research 实例化**：当前仅落地 schema，后续需在科研工作流中生成实际的 envelope 实例并验证 research_specific 字段的可用性。
2. **smoke 骨架扩展**：当前骨架覆盖 8 条基础测试用例，后续需随科研 Agent 体系扩展补充更多场景化断言（如 retraction-check skill 可用性、experiment_log_ref 完整性等）。
3. **13 方法论的代码级落地**：当前 methodology-integration 文档完成方法论→角色/Gate 的映射，部分方法论（如风格指纹量化、认知投降检测）标注为「未来迭代」，需后续迭代补全。
4. **跨分支回流**：将 research-team 的 7-mode 完整性 gate 经验回流至 main 分支的 quality-scoring hard_disqualifiers，待 main 分支确认后执行。
5. **Gate 通过条件自动化验证**：当前 pass_conditions 为文字描述，后续需在 harness 层实现可编程的通过条件检查器。

---

版本：v1.0
日期：2026-07-02
