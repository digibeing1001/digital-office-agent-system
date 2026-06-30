# 科研团队:评分 + 反思 + 自我进化机制

这份文档说明科研团队的每个 Agent 如何被评分、如何反思改进、如何跨项目积累经验自我迭代。

## 一、为什么需要这套机制

LLM 自评会高估自己(论文 Si et al. 2024 已证实)。所以:
- 评分不能只靠 LLM 内省,必须混合外部工具核查(CRITIC 范式)
- 返工不能简单重跑,必须先生成反思再带着反思重写(Reflexion 范式)
- 经验不能只存当前会话,必须跨项目沉淀复用(ExpeL 范式)

## 二、评分卡(科研专用)

### 六维评分,满分 100,合格 75

| 维度 | 权重 | 含义 | 工具核查 | 一票否决 |
|---|---|---|---|---|
| 严谨性 | 25 | 方法正确、实验充分、引用真实 | 引用核查 + 可复现性 + 统计显著性 | 是 |
| 新颖性 | 20 | 与已有工作的区别 | 文献比对 | 是 |
| 清晰度 | 20 | 表达清楚、图表规范 | 语法 + 格式检查 | 否 |
| 可行性 | 15 | 资源/时间/数据可得性 | 资源评估 | 是 |
| 影响力 | 10 | 问题价值 | — | 否 |
| 置信度 | 10 | 评分者自评置信度 | — | 否 |

**一票否决**:任一标"是"的维度得分 < 50%,即使总分过 75 也直接返工。

### 评分依据
- NeurIPS/ICLR/ACL 审稿 rubric(严谨性/新颖性/清晰度/影响力)
- Si et al. 2024(arXiv:2409.04109)idea 六维评估(加可行性/兴奋度)
- AI-Scientist 的 perform_llm_review.py 评审 prompt

配置文件:[scoring_config.yaml](../profiles/office-research-secretary/scoring_config.yaml)

## 三、三类反思进化场景

### 场景 1:用户纠正 → 内化为长期偏好

用户说"以后查文献不要只用 Google Scholar"这类纠正时:

```
用户纠正
  → 偏好内化器判断:通用偏好 还是一次性指正?
    通用 → 写入该 Agent 的 SOUL.md(标日期+来源)
          格式:[用户偏好 2026-07-01] 文献检索必须先查 ACM Digital Library
    一次性 → 存入当前项目 checkpointer,不污染长期记忆
```

依据:Reflexion 的反思文本 + mem0 的偏好持久化

### 场景 2:秘书评分不合格 → 返工 + 记录返工原因

```
秘书评分 < 75(或某维一票否决)
  → Reflector 生成反思文本(Reflexion 式)
      反思内容:哪个维度不够、为什么不够、下次怎么改
  → 反思存入 checkpointer(单会话)
  → Actor 带反思重写
  → 若同一维度连续返工 >= 2 次
      → 升级为 anti-pattern,写入经验库(跨会话)
      → 标注:"遇到 X 情况,不要 Y"
```

返工最多 3 轮,超 3 轮上报用户决策。

### 场景 3:项目跑完 → 沉淀经验

```
项目结束
  → 经验抽取器(ExpeL 式)扫描整轮轨迹
  → 抽取 insights:
      成功方案 → "遇到 X 情况,应该 Y"
      失败教训 → "遇到 X 情况,不要 Y"
  → 去重(与现有经验库比对)
  → 写入 skills/experience/<agent_id>/<topic>.md
  → 更新 scoring_config(若发现某维度评分系统性偏差)
```

新项目启动时,按主题相似度检索 top-5 经验注入 Agent 的 system prompt。

## 四、单会话反思 vs 跨会话经验

| | 单会话反思 | 跨会话经验 |
|---|---|---|
| 生命周期 | 一个项目内,返工轮次间 | 跨项目,永久 |
| 存哪 | checkpointer / 对话上下文 | skills/experience/ + BaseStore |
| 粒度 | "这次第 2 步检索漏了 X" | "做综述类任务时,先查 survey 再查原文" |
| 触发 | 每次返工自动触发 | 项目结束/用户纠正时触发抽取 |

两者不是二选一,都做。

## 五、三件套存储结构

### A. SOUL.md — 性格与长期偏好
- 存:角色定位、硬规则、用户长期偏好(被纠正后内化的)
- 改写时机:用户明确纠正后,由偏好内化器 append
- 只放稳定规则,不塞具体项目经验

### B. skills/experience/ — 可复用经验库
- 存:成功方案、失败教训(anti-pattern)
- 结构:`skills/experience/<agent_id>/<topic>.md`
- 新项目启动时按相似度检索 top-5 注入 prompt

### C. scoring_config.yaml — 可调阈值
- 存:评分卡权重、合格线、返工最大轮数
- 进化:经验回顾器定期根据历史返工率微调建议(人工确认后生效)

## 六、每个 Agent 的反思进化能力

所有 10 个角色都具备:
1. **被评分时**:接收评分卡 + 反思文本,带反思重写
2. **被用户纠正时**:判断通用/一次性,内化到 SOUL.md 或 checkpointer
3. **项目结束时**:经验抽取器从轨迹抽取 insights,存入经验库
4. **新项目启动时**:按主题检索经验库 top-5,注入 system prompt

## 七、技术栈建议

| 组件 | 推荐 | 用途 |
|---|---|---|
| 记忆骨架 | LangGraph(checkpointer + BaseStore) | 返工记忆 + 跨项目经验 |
| 偏好持久化 | SOUL.md(纳入 system prompt) | 用户纠正内化 |
| 经验检索 | BaseStore 向量检索 或 mem0 | top-k 经验注入 |
| 评分引擎 | 评分卡 + CRITIC 工具核查 | 避免纯 LLM 自评幻觉 |
| 提示词自优化 | DSPy(可选,进阶) | 按评分自动迭代 few-shot |

## 八、论文依据

| 机制 | 论文 | arXiv |
|---|---|---|
| 返工带反思 | Reflexion(Shinn et al. NeurIPS 2023) | 2303.11366 |
| 自反馈精炼 | Self-Refine(Madaan et al. NeurIPS 2023) | 2303.17651 |
| 跨任务经验抽取 | ExpeL(Zhao et al. AAAI 2024) | 2308.10144 |
| 工具核查防幻觉 | CRITIC(Gou et al. ICLR 2024) | — |
| 多 Agent 辩论 | Multiagent Debate(Du et al. ICML 2024) | 2305.14325 |
| 技能库复用 | Voyager(MineDojo) | — |
| idea 评估维度 | Si et al. 2024 | 2409.04109 |
| 自动评审 | AI-Scientist(SakanaAI) | 2408.06292 |
| 模拟同行评审 | AgentReview(NeurIPS 2024) | — |

## 九、关键提醒

1. **LLM 自评不可信**:评分必须混合工具核查(CRITIC)
2. **经验库会膨胀污染**:必须做去重和衰减(ExpeL 的做法)
3. **SOUL.md 只放稳定规则**:别塞具体项目经验
4. **返工不是简单重跑**:必须先生成反思再重写
5. **跨会话经验需人工确认**:anti-pattern 写入经验库前建议人工 review
