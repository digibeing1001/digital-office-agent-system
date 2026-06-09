# 数字办公室 Agent System

> 把 AI Agent 变成你的数字员工团队 — 秘书、产品经理、研究员、规划师、设计师、工程师、写手，各司其职，协同交付。

数字办公室是一套**可分发的多 Agent 办公运行层**。部署到 [Hermes](https://hermes-agent.nousresearch.com)、OpenClaw 或其他兼容 Agent 宿主后，它将宿主默认 Agent 注入为“数字办公室秘书”，由秘书统一完成需求收口、角色路由、工作流编排、知识边界、质量门禁和交付说明。

用户不需要理解底层 Agent 工具 — 你只需要描述需求，秘书会安排合适的数字员工接手。

---

## AI Native Loop（核心运行原则）

数字办公室的每一项任务都遵循 **Perceive → Plan → Execute → Reflect → Iterate** 五步闭环。这不是某一条工作流，而是整个产品的基础运行逻辑：

| 阶段 | 名称 | 做什么 |
|------|------|--------|
| 1 | **感知** | 收集用户意图、项目上下文、知识来源、权限和路由候选 |
| 2 | **规划** | 选择角色、编排工作流、定义验收标准和回滚方案 |
| 3 | **执行** | 通过路由器调度 Agent，记录产物、观测和门禁结果 |
| 4 | **反思** | 对照计划和证据审查结果，生成问题发现和方法改进建议 |
| 5 | **迭代** | 系统可提出改进提案，但**必须等用户确认后才能应用** |

关键约束：
- **迭代永远不是自动的** — 任何规则、工作流、Agent 行为、知识库的变更都必须先生成用户可见提案，等用户确认后才应用
- **生产声明需要确定性门禁 + 反思报告双重验证** — 没有通过 harness 检查的任务不能标记为完成
- **秘书拥有最终责任** — 模糊路由、用户确认、迭代提案和失败门禁恢复都由秘书负责

这条原则被硬编码在 gent-system/ai-native-loop.manifest.json 中，秘书能力配置 secretary.capabilities.json 专门定义了 loop policy，并有独立的 harness 生产门禁 i-native-loop-production.json 验证其完整性。它约束着所有工作流的执行方式，包括 PPT 生产、Vibe Design、Vibe Coding 等。

---

## 它能做什么

### 多 Agent 协作

内置 7 个数字员工角色，通过统一注册表协作：

| 角色 | 职责 |
|------|------|
| **秘书** | 需求澄清、任务路由、交接管理、最终交付 |
| **产品经理** | 产品判断、PRD、路线图、优先级 |
| **研究员** | 市场调研、竞品分析、事实验证 |
| **规划师** | 架构设计、方案规划、里程碑拆解 |
| **设计师** | 视觉方向、UI 设计、原型 |
| **工程师** | 编码、调试、测试、部署 |
| **写手** | 文案、故事线、讲稿、文档 |

用户说出需求，秘书自动选择合适的角色组合，管理多 Agent 交接，确保后续角色使用前序产物而不是从头开始。

### 工作流引擎

内置可扩展的工作流控制面，支持：

- **PPT 生产** — intake → writing → design → delivery，从需求澄清到交付完整 deck
- **Vibe Design** — 设计类任务的生产门禁保障
- **Vibe Coding** — 编码类任务的 TDD + 质量审查

所有工作流都在 AI Native Loop 框架内执行，遵循感知 → 规划 → 执行 → 反思 → 迭代的五步闭环。

### 知识与记忆管理

分层知识体系，避免把草稿当事实：

1. **项目知识库** — 当前项目的文档、决策、素材（最高优先级）
2. **公司知识库** — 组织级方法论、模板、标准
3. **授权行业参考层** — 按权限挂载的行业知识
4. **KeyMemory 接力记忆** — 跨会话、跨 Agent 的语义接力

### 质量门禁

每个生产任务必须通过 harness-check 和 harness-runner 验证：

- 路由正确性
- 工作流闭环
- 知识权限合规
- GUI 契约一致性
- 生产门禁通过

### 用户确认式迭代

系统**不允许静默自我修改**。任何规则、工作流、Agent 行为、知识库的改进，都必须先生成迭代提案，等用户确认后应用。

---

## 快速开始

### 安装

\ash
git clone https://github.com/digibeing1001/digital-office-agent-system.git
cd digital-office-agent-system

# 安装到 Hermes
./install.sh --host hermes --target ~/.hermes

# 安装到 OpenClaw
./install.sh --host openclaw --target ~/.openclaw
\n
安装器会自动：
- 注入数字办公室秘书入口到宿主默认 Agent
- 同步 agent-system、scripts、profiles、skills 和产品文档
- 运行健康检查验证安装完整性

### 已有宿主的安装选项

如果目标宿主已有个人规则或数据，安装器不会静默覆盖：

\ash
# 保留原规则，旁路安装
./install.sh --host openclaw --target ~/.openclaw --preserve-existing

# 备份原入口后覆盖
./install.sh --host openclaw --target ~/.openclaw --overwrite-existing
\n
### 使用

安装完成后，直接向宿主 Agent 描述需求即可。秘书会自动接管并路由到合适的数字员工：

\n> 帮我做一份竞品分析的 PPT 汇报
> 帮我调研一下东南亚市场的 SaaS 机会
> 写一个产品需求文档
> 帮我重构这个 Python 模块
\n
---

## 支持的宿主

| 宿主 | 默认目标目录 | 注入入口 | 默认 Agent 角色 |
|------|-------------|---------|----------------|
| [Hermes](https://hermes-agent.nousresearch.com) | \~/.hermes\ | \SOUL.md\ | secretary |
| OpenClaw | \~/.openclaw\ | \AGENTS.md\ | secretary |
| generic | \~/.digital-office-agent\ | \AGENTS.md\ | secretary |

---

## 面向开发者

### 架构概览



### 仓库结构



### 核心设计原则

1. **Portable Role 优先** — 不把 Agent 名称写死到产品逻辑。先选择 portable role，再从注册表映射到具体 Agent。
2. **知识分层** — KeyMemory 是接力记忆层，不是事实源。项目知识库 > 公司知识库 > 行业参考 > KeyMemory。
3. **用户确认** — 不允许系统静默自我迭代。任何变更必须生成提案，等用户确认。
4. **GUI 契约** — 所有后端能力必须有 GUI 命令合约，不只提供 CLI。
5. **本地优先** — 模型权重不提交到仓库，部署时由安装器下载到客户主机。

### 开发验证

提交前运行：

```bash
# 语法检查
python3 -m py_compile agent-system/bin/office-system.py \\
  agent-system/bin/harness-check \\
  agent-system/bin/harness-runner \\
  scripts/agent-router

# 门禁检查
agent-system/bin/harness-check
agent-system/bin/harness-runner --task all --no-write

# 冒烟测试
bash agent-system/tests/smoke.sh
```

### 路由测试

```bash
# 查看路由健康状态
scripts/agent-router --health

# 测试路由决策
scripts/agent-router --route-json "帮我做一份PPT汇报"
scripts/agent-router --route-json "research competitors and design the interface"
```

### GUI 后端入口

```bash
# 首页总览
agent-system/bin/office-system gui-state --user <user_id> --project <project_id>

# Onboarding
agent-system/bin/office-system onboarding-options
agent-system/bin/office-system onboarding-apply --assistant-style neutral_operator ...

# 设置
agent-system/bin/office-system settings-status
agent-system/bin/office-system settings-update --work-mode quality --confirmed

# Web UI
agent-system/bin/office-system web-serve --host 127.0.0.1 --port 8787
```
---

## 关键文档

| 文档 | 说明 |
|------|------|
| [architecture.md](agent-system/docs/architecture.md) | 总体架构、运行层、知识模型、发布模型 |
| [host-rule-injection.zh-CN.md](agent-system/docs/host-rule-injection.zh-CN.md) | 宿主注入策略详解 |
| [ppt-production-workflow.md](agent-system/docs/ppt-production-workflow.md) | PPT 生产工作流与角色边界 |
| [production-harness.md](agent-system/docs/production-harness.md) | 生产门禁设计 |
| [gui-contract.md](agent-system/docs/gui-contract.md) | GUI 与本地运行层的命令合约 |

---

## 合规说明

本系统默认关闭行业经验数据分享（`industry_experience_sharing: false`），符合《个人信息保护法》（PIPL）和 GDPR 的数据最小化原则。如需开启，请通过 Web UI 或 CLI 明确确认。

---

## 开发进度

详见 [CHANGELOG.md](CHANGELOG.md)。

---

## 参考与致谢

本系统的工程原则参考了以下方向：

- **ReAct** — action / observation 循环
- **Reflexion** — 反思反馈机制
- **Generative Agents** — 记忆 / 反思 / 规划分层
- **Voyager** — 可复用技能库
- **MetaGPT / AutoGen** — 多 Agent 角色协作
- **LangGraph** — 持久执行与 human-in-the-loop
- **SWE-agent / OpenHands** — 编码 Agent harness
- **RAGAS / Self-RAG** — 检索质量与自我评估

---

## 许可

Private — 当前为内部开发通道。生产客户应接收经过验证的发布包。
