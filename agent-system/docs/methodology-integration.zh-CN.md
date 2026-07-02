# 方法论集成 · writer-team 13 方法论 → research-team 适配

> 本文档记录 writer-team `workflow/qa-framework.md` v1.1 中 13 个方法论吸收项如何适配到 research-team 的科研完整性场景。
> 来源：三分支相互学习 2026-07 迭代。
> 参考文件（只读）：`wt-writer/workflow/qa-framework.md` v1.1。

---

## 适配原则

writer-team 的 13 个方法论围绕「写作 QA」设计，核心是把定性检查升级为可度量机制。research-team 的对应物是「科研完整性门控」——不评估文章好不好读，而评估研究可不可信。适配时遵循三条原则：

1. **保留方法论内核**：偏见消除 / 原子化核查 / 工具增强 / 可演进 evals 等思想不变。
2. **替换场景锚点**：把「读者价值」替换为「研究可信度」，把「文章审查」替换为「完整性 gate」。
3. **映射到现有策略文件**：不新增角色，方法论落实到 `research-integrity-gates.policy.json` / `coordination.policy.json` / `quality-scoring.policy.json` 的已有字段。

---

## 13 方法论适配表

| # | 方法论 | 原始场景（writer-team） | research-team 适配 | 落地位置 |
|---|---|---|---|---|
| 1 | LLM-as-judge 三类偏见消除（arxiv: 2306.05685, 2305.17926） | 写作 Agent 与审查 Agent 同源时纵容自身缺陷；引入异质审查者消除位置偏见/冗长偏见/自我偏好偏见 | 研究 Agent 与审查 Agent 必须异质（不同 instance / 不同模型家族）；引用核查、方法论审查不能由生成模型自审 | `research-integrity-gates.policy.json` → `cross_model_verification.strategy`（judge_model 不同家族，min_models ≥ 2）；`quality-scoring.policy.json` → `debiasing.maker_checker_isolation` |
| 2 | FActScore 原子化事实核查（arxiv: 2305.14251） | 把文章拆成原子命题，逐条标记 ✅ 已验证 / ⚠️ 单一信源 / 🔴 错误存疑 | 每条引用通过 Semantic Scholar API 验证 existence + 非撤稿，逐条标注 ✅/⚠️/🔴；不止记编号，还要标注每条的支持状态 | `research-integrity-gates.policy.json` → `hallucinated_citation` gate（required_outputs: `citation_verification_report` + ✅/⚠️/🔴标注；pass_conditions: 所有引用 ✅ 或单一信源 ⚠️ 已声明，无 🔴） |
| 3 | CRITIC 工具增强审查（arxiv: 2305.11738） | 事实类声明用搜索工具核查，数据类用计算工具验证，不靠模型脑补 | 引用核查用 Semantic Scholar API，撤稿检查用 PaperQA2 / Crossref 撤稿标记，数据复现用计算脚本验证数字一致性 | `research-integrity-gates.policy.json` → `retracted_source_dependency` gate（required_outputs: `retraction_check_report`）+ `data_fabrication` gate（required_outputs: `data_provenance_log` + `原始数据哈希`） |
| 4 | Evals 可演进（吴恩达原话 + Promptfoo CI/CD） | 反复踩坑的场景固化为 evals；定期复盘失效的 eval 并更新 | 每次完整性 gate 触发后，将失效模式固化为新的检查项；gate escalation 机制把连续触发升级为经验库教训 | `research-integrity-gates.policy.json` → `scoring_trajectory_tracking`（跟踪趋势/波动/停滞/回退）+ 每个 gate 的 `escalation` 字段（连续 2 次触发 → 升级为经验库教训 + human_gate） |
| 5 | MT-Bench 多轮体验衰减（arxiv: 2306.05685） | 读者价值不只看开头钩子，做三段式体验扫描（开头/中段/结尾） | 论文论证链不能中段断裂：假设 → 证据 → 结论的逻辑密度需持续，中段证据稀疏 = 论证衰减 | `quality-scoring.policy.json` → `role_gates.research.rubric_items`（论证连贯性检查）；`research-integrity-gates.policy.json` → `claim_overgeneralization` gate（claim 范围不能超出实验覆盖） |
| 6 | Helpful-Honest-Harmless 三维价值框架（arxiv: 2204.05862） | 读者价值 = Helpful × Honest × Harmless，任一为 0 总分归零 | 研究产出 = 有用（可复现）× 诚实（无幻觉引用/无数据伪造）× 无害（不误导后续研究）；任一维度 gate 失败 = 交付阻断 | `research-integrity-gates.policy.json` → 7-mode gates 覆盖三维：Honest（hallucinated_citation / data_fabrication / retracted_source_dependency）、Helpful（reproducibility_gap）、Harmless（claim_overgeneralization / framework_lock_in） |
| 7 | 多 Agent 辩论收敛（arxiv: 2305.14325） | 读者价值层 QA 做多视角博弈（审查员/秘书/作者/模拟读者），反对意见显式记录 | PI / 方法学家 / 审查员多视角辩论框架选择与结论强度；框架相似度 > 0.8 时必须声明差异或引用先行工作 | `coordination.policy.json` → `parallel_expert_dag` mode（多 Agent 独立工作后合成）；`research-integrity-gates.policy.json` → `framework_lock_in` gate（block_on: 框架与已有工作相似度 > 0.8 且未声明差异） |
| 8 | 个性化评判标准（Personalized Evaluation） | 读者画像不同，评判标准动态调整（专业读者 vs 大众读者） | 研究领域不同，完整性 gate 的严格度可配置：临床研究 max_rework=0（零容忍），探索性研究 max_rework=2（允许迭代） | `research-integrity-gates.policy.json` → 每个 gate 的 `max_rework` 字段（data_fabrication=0 不可协商，其余=2 允许返工）；`cross_model_verification.strategy.agreement_threshold`（0.8 可按领域调整） |
| 9 | Reflexion 情景记忆（arxiv: 2303.11366） | 每篇文章交付后生成「本次踩坑反思」，写入风格库，下一篇先读取 | 每次 gate 触发后生成失效模式反思，升级为经验库教训；连续触发同一 gate = Agent 在该维度未进化 | `research-integrity-gates.policy.json` → 每个 gate 的 `escalation` 字段（连续 2 次触发 → 升级为经验库教训 + human_gate / 降级 Agent 置信度）；`scoring_trajectory_tracking.analysis.regression`（评分从 pass 降到 fail 时标记回退） |
| 10 | Self-Rewarding 自我进化（arxiv: 2401.10020） | 写作 Agent 每篇交付后做自评（撰稿人/审查员/风格官各自元认知） | 研究 Agent 每次交付后做自评：方法学家评方法论适用性，文献研究员评引用覆盖度，数据分析师评数据可追溯性 | `research-integrity-gates.policy.json` → `scoring_trajectory_tracking.analysis`（trend 线性回归斜率正数=改善，volatility 最近 3 次评分标准差，stagnation 连续 N 次变化 < 0.02 标记停滞） |
| 11 | 风格指纹量化（StyleLLM，GitHub 1k+ Star） | 把「风格」从主观感受量化为可计算指纹（句长分布/虚词频率/标点偏好/语义模式） | 把「研究风格」量化：引用密度（每千字引用数）、方法描述粒度（步骤可追溯率）、数据呈现规范（图表/统计检验完整性） | `quality-scoring.policy.json` → `role_gates.research.rubric_items`（引用密度/方法描述粒度/数据呈现规范作为评分项）；`research-integrity-gates.policy.json` → `fabricated_method` gate（required_outputs: `methodology_checklist` + 统计方法适用性评估） |
| 12 | ExpertPrompting 身份条件生成（arxiv: 2305.14688） | 审查员不以「通用质检员」身份审查，以「目标读者画像」身份审查 | 审查时以目标领域专家身份审查：临床研究由临床统计学家审，实验研究由实验设计师审；cross_model_verification 的 judge_model 注入领域专家身份 | `research-integrity-gates.policy.json` → 每个 gate 的 `applies_to_roles` 字段（如 fabricated_method → methodologist / research-engineer）；`cross_model_verification.strategy.judge_model`（不同家族模型 + 领域身份注入） |
| 13 | 「认知投降」检测（Addy Osmani 三种认知风险） | 作者越来越快点「通过」Gate / 终稿修改 diff 持续减少 → 警惕认知投降 | PI 越来越少质疑 Agent 结论 / 越来越少做方法论拍板 → 警惕；科研判断权不能让渡给 AI，data_fabrication gate 零容忍正是此原则的硬约束 | `coordination.policy.json` → `human_gated` mode（高风险工作必须人工判断）；`research-integrity-gates.policy.json` → `data_fabrication` gate（max_rework=0，立即 human_gate + 伦理员介入）；所有 gate 的 `max_rework` 上限防止无限自我修正 |

---

## 三层 QA → 三层科研完整性映射

writer-team 的三层 QA（执行层 / 读者价值层 / 长期竞争力层）对应 research-team 的三层完整性保障：

| writer-team 三层 QA | research-team 三层完整性 | 对应方法论 |
|---|---|---|
| 第一层 · 执行层（挑错型，审查员承载） | 第一层 · 引用与方法核查（hallucinated_citation / fabricated_method / data_fabrication / retracted_source_dependency） | 吸收 1 LLM-as-judge 偏见消除、吸收 2 FActScore 原子化、吸收 3 CRITIC 工具增强 |
| 第二层 · 读者价值层（PM 型，秘书+审查员升级） | 第二层 · 论证与框架核查（framework_lock_in / claim_overgeneralization / reproducibility_gap） | 吸收 5 MT-Bench 衰减检测、吸收 6 HHH 三维框架、吸收 7 多 Agent 辩论、吸收 8 个性化评判 |
| 第三层 · 长期竞争力层（战略型，风格官+作者承载） | 第三层 · 经验沉淀与进化（scoring_trajectory_tracking / cross_model_verification / escalation） | 吸收 4 可演进 evals、吸收 9 Reflexion、吸收 10 Self-Rewarding、吸收 11 风格指纹、吸收 12 ExpertPrompting、吸收 13 认知投降检测 |

---

## 与 writer-team 的差异说明

writer-team 的方法论以「文章质量」为锚点，research-team 以「研究可信度」为锚点。关键差异：

1. **data_fabrication 零容忍**：writer-team 的 data_fabrication 对应物是「数据引用错误」，可返工；research-team 的数据伪造是伦理红线，max_rework=0 直接 fail + 伦理员介入。
2. **retracted_source_dependency 硬阻断**：writer-team 不专门检查撤稿论文；research-team 必须通过 PaperQA2 / Crossref 检查撤稿标记，核心论点依赖撤稿论文 = 阻断。
3. **framework_lock_in 领域特化**：writer-team 的 framework_lock_in 检查写作框架雷同；research-team 检查研究框架与近 2 年已发表框架相似度 > 0.8。
4. **cross_model_verification 更严格**：writer-team 关键产出交叉验证；research-team 在 final_delivery / integrity_gate_triggered / human_gate_requested 三个节点强制交叉验证，min_models ≥ 2，agreement_threshold 0.8。

---

## 版本

- v1.0 · 2026-07-02 · 三分支相互学习 2026-07 迭代产出
- 参考来源：`wt-writer/workflow/qa-framework.md` v1.1（13 方法论吸收）
