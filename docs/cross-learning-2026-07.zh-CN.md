# 三分支相互学习记录 · 2026-07

> 版本：v1.0 ｜ 日期：2026-07-02
> 范围：digital-office-agent-system 仓库三个并列分支（main / research-team / writer-team）的设计经验互鉴
> 本文档由 writer-team 分支维护，记录本次相互学习在 writer-team 的落地清单与后续待跟进事项。

---

## 一、背景

digital-office-agent-system 仓库下存在三个并列分支，各自承担不同的系统设计目标，互不替代、互不背离：

- **main 分支（数字办公系统）**：承载「三层员工模型」——秘书控制面 → 数字员工 → 技能 staff lanes，定位为通用数字办公底座。其 profile SOUL.md 模板与 `skills/_imported/taste-skill/` 是本次 writer-team 的主要学习来源之一。
- **research-team 分支（科研团队）**：定位为科研秘书 + PI + 工程师的科研协作系统。其 `skills/verification-loops/` 与 `skills/cross-model-verification/` 两个 skill，以及 `agent-system/research-integrity-gates.policy.json` 的 scoring_trajectory 设计，是本次 writer-team 的主要学习来源之二。
- **writer-team 分支（写作团队）**：定位为写作 Agent Team，以 8 角色 + 6 Gate + 去 AI 味三重保障为核心。本次迭代吸收 main 与 research-team 的设计经验，强化自身的「解耦 judge / 趋势跟踪 / SOUL 身份段 / 反 AI Slop」能力。

三方在不背离各自设计目标的前提下相互学习：main 提供「SOUL 模板 + taste-skill」，research-team 提供「解耦 judge + scoring_trajectory + SOUL 模式」，writer-team 反向输出「三层 QA 框架 + Gate 防跳协议」供另两方参考。本文档记录本次相互学习在 writer-team 的落地。

---

## 二、学习矩阵

| 来源 → 目标 | 学到的经验 |
|---|---|
| main → writer-team | taste-skill（反 AI Slop 检查，14 子 skill）——把「检测 AI 生成内容的冗余/套话/结构化套路」从写作侧的「去 AI 味三重保障」扩展到更系统的 anti-slop 模式库，登记为 referenced，待后续正式接入 |
| main → writer-team | profile SOUL.md 模板（身份 / 思维方式 / 禁区结构）——把角色卡从「职责驱动」升级为「身份先行」，先回答「我是谁、我怎么想、我不做什么」，再回答「我做什么」 |
| research-team → writer-team | verification-loops + cross-model-verification（解耦 judge 防自评偏差）——用「模型家族隔离 / judge 盲审 / 多样本投票」三硬约束，强化 writer-team QA 第一条方法论「LLM-as-judge 三类偏见消除」的硬约束层 |
| research-team → writer-team | research-integrity-gates 的 scoring_trajectory 设计——把 writer-team 第三层 QA「长期竞争力层」从定性检查升级为趋势可监测（trend / volatility / stagnation / regression 四指标） |
| research-team → writer-team | SOUL.md 模式（身份 / 思维方式 / 边界 / 反思与进化）——为秘书角色卡增加 SOUL 段，把「不替专岗干活 / 不绕过审批 / 灰色地带不独断」沉淀为身份层硬约束 |
| writer-team → main / research-team | 三层 QA 框架（执行层 / 读者价值层 / 长期竞争力层）+ Gate 防跳协议——反向输出「QA 横切三层 Loop」与「不可逆动作阻断门」方法论，供另两方参考（本次仅 writer-team 侧落地，另两方待各自迭代时酌情吸收） |

---

## 三、writer-team 本次落地的 5 项迭代清单

| # | 任务 | 落地文件 | 变更摘要 |
|---|---|---|---|
| 1 | 新建相互学习记录文档 | `docs/cross-learning-2026-07.zh-CN.md` | 新建 docs/ 目录与本文档，记录三分支学习矩阵与落地清单 |
| 2 | QA 框架新增附录 A | `workflow/qa-framework.md` | 新增「附录 A：解耦 judge 防自评偏差」，3 条硬约束（模型家族隔离 / judge 盲审 / 多样本投票） |
| 3 | QA 框架新增附录 B | `workflow/qa-framework.md` | 新增「附录 B：scoring_trajectory 趋势跟踪」，4 项监测指标与阈值建议 |
| 4 | 外部技能清单新增 taste-skill | `workflow/external-skills.md` | 新增 taste-skill 技能条目（P0 必备，referenced 状态）+「附录：taste-skill 接入说明」 |
| 5 | 秘书角色卡新增 SOUL 段 | `agents/00-secretary.md` | 顶部新增「SOUL（身份 · 思维方式 · 禁区）」段，含身份 / 思维方式 / 禁区 / 能力从哪来 4 子段 |

---

## 四、后续待跟进事项

1. **taste-skill 正式接入**：当前登记为 referenced，仅完成方法论引用。后续需评估 14 个子 skill 中哪些可改造为中文写作侧的 anti-slop 检查项，正式接入审查员 / 风格官工作流。
2. **解耦 judge 接入工具层**：附录 A 的 3 条硬约束目前为方法论层，后续需在工具层落地「模型家族注册表 + judge 盲审协议 + 多样本投票脚本」，与 research-team 的 `model-providers.registry.json` 对齐。
3. **scoring_trajectory 数据落地**：附录 B 的 4 项指标目前为阈值建议，后续需在风格库建立「评分轨迹」章节，按篇追加评分记录，季度复盘时计算 trend / volatility / stagnation / regression。
4. **SOUL 段下沉到其他角色卡**：本次仅在 `00-secretary.md` 增加 SOUL 段。后续按 research-team SOUL.md 模式，为审查员 / 撰稿人 / 风格官等角色卡补充 SOUL 段，统一「身份先行」的角色卡结构。
5. **反向输出待对齐**：writer-team → main / research-team 的「三层 QA + Gate 防跳协议」反向输出目前仅记录在本文档，待另两方分支迭代时由各自维护者酌情吸收，不在 writer-team 侧强制推进。

---

版本：v1.0 ｜ 日期：2026-07-02 ｜ 维护分支：writer-team
