# UI 界面设计前置就绪说明

本文记录正式开始 UI 设计前，后端和运行契约必须满足的条件。

## 最终产品结构

数字办公室采用稳定的二层 Agent 模型：

1. 用户通过秘书 Agent 下达任务。
2. 秘书把任务交给特定工作的数字员工 Agent。
3. 每个数字员工 Agent 可以代表一个业务部门负责人。
4. 该业务部门下面的员工不是 Agent，而是一个个 Skill。

也就是说，`Agent` 是产品可见的责任主体，`Skill` 是内部执行能力。UI 可以用“部门”帮助用户理解业务边界，但不能把部门画成多层 Agent 组织树。

## 已固化的后端契约

- `agent-system/digital-employees.registry.json`：产品可见数字员工清单。
- `agent-system/workflow-packs.registry.json`：每个数字员工可运行的工作流包和 Skill lanes。
- `agent-system/context-envelope.schema.json`：跨 Agent、跨 Skill、跨阶段上下文流转信封。
- `agent-system/skill-installations.registry.json`：本地已安装 source pack 和许可证阻断状态。
- `agent-system/agents.registry.json`：运行时 Agent、路由、模型、profile 和 workflow 真相来源。

## 法务形态

法务不再是“法务部门 Agent + 合同 Agent + 合规 Agent”的多层结构。

正式形态是一个数字员工：

- Agent id：`legal`
- 用户可见名称：数字律师
- 业务身份：企业内设法务负责人
- 内部员工：合同审查、公司法、隐私数据、产品合规、用工/IP、争议分流、AI 治理等 Skill lanes

数字律师产出均为企业内部审查草稿。外部函件、签署、产品上线、用工动作、诉讼仲裁等高风险行为必须经过人工专业复核。

## 上下文流转要求

UI 工作流不能把大段上下文在节点之间复制粘贴。它必须围绕 context envelope 设计：

- `goal`：本次任务目标
- `user_intent`：用户真实意图
- `constraints`：限制条件
- `acceptance_criteria`：验收标准
- `source_refs`：项目、公司、授权来源或外部链接
- `artifact_refs`：文件、草稿、运行产物
- `decisions`：已做决定
- `open_questions`：未决问题
- `risk_flags`：风险标记
- `permissions`：租户、项目、用户、角色和允许动作
- `state_hash`：当前状态摘要

UI 可以把这些字段呈现为任务详情、节点上下文、交接卡片、风险面板和证据面板。

## 本地 Skill 安装状态

已落地：

- `claude-for-legal-zh`：Apache-2.0，已安装到 `skills/_imported/claude-for-legal-ZH`，通过 `digital-lawyer-workflows` 受控使用。

被阻断：

- `Legal-Skills-Chinese`：CC BY-NC-ND 4.0，未获得商用许可前不得激活、改编、内置到商用工作流或再分发。

## UI 可以开始设计的条件

开始视觉 UI 设计前，以下命令必须通过：

```bash
agent-system/bin/install-skill-sources
agent-system/bin/harness-check
agent-system/bin/harness-runner --task ui-design-readiness-production --no-write
agent-system/bin/harness-runner --task all --no-write
```

若其中任意一项失败，优先修后端契约，不进入视觉设计。
