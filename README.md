# 数字办公室 Agent System

这是一套基于 Hermes 的数字办公室底层系统。它不是一个只靠命令行使用的 Agent 配置包，而是面向未来 GUI 产品的多 Agent 运行层：用户在界面里创建项目、上传知识、分派任务、查看 Agent 协作、确认迭代和接收交付；Hermes 在底层负责 Agent 执行、路由、技能调用、知识读取和本地模型能力。

这套系统的目标是把“一个人使用 AI 工具”升级为“一个人或一个团队管理一间数字办公室”。它可以迁移到数字律所、数字会计师事务所、数字新媒体工作室、一人公司开发者工作台、一人设计师工作台等不同业务场景。

## 产品特点

- 多 Agent 办公室：秘书、PM、研究员、规划师、设计师、工程师、写作者等数字员工通过统一注册表和路由器协作。
- 智能路由：`scripts/agent-router` 读取 `agent-system/agents.registry.json`，先判断任务所需角色，再映射到当前部署的 Agent，避免把产品逻辑硬编码到某几个 Agent 名称上。
- 工作流控制面：普通用户从 GUI 发起任务时，系统会同时创建 WorkflowRun、任务记录、权限决策、审计事件和通知，而不是只把一句话丢给 Agent。
- 任务台与审批中心：任务可以排队、阻塞、等待审批、完成、失败、取消；高风险动作通过审批中心确认，审批通过或拒绝都会回写任务和工作流状态。
- 权限、审计和通知：工作流启动、任务更新、审批决策等关键动作都会经过角色权限判断，并写入带 hash 链的审计日志，GUI 可以展示通知和未读提醒。
- AI native 闭环：每个生产任务按照“感知、规划、执行、反思及迭代”推进，并留下可回放记录。
- 显式迭代：系统可以提出改进建议，但不能未经用户确认就自我修改。迭代必须显示变更内容、原因、影响、风险、回滚和回归检查。
- 双层知识库：公司全局知识库保存长期方法论和组织规则，项目知识库保存项目资料、过程文件和阶段决策。
- KeyMemory 接力记忆：KeyMemory 用来承接项目和子项目之间的交接、偏好、摘要和检索指针，不作为项目事实的最高来源。
- 多模态知识预留：支持 PDF、Word、文本和图片上传；本地 OCR/RAG 模型在部署时下载，不把模型权重提交到仓库。
- 行业知识库和权限：支持将供应商销售的行业知识库作为授权参考层挂载到项目、公司或特定 Agent，不允许用户下载源文件。
- 生产 harness：通过 `harness-check` 和 `harness-runner` 检查路由、知识、技能、闭环、GUI 契约、迭代确认和回归任务。
- 企业发布预留：普通用户只看到数字办公室 GUI；Hermes、本地模型、Agent 插件和 skill 更新由我们验证后通过产品发布渠道推送。

## 架构概览

```text
用户 / 企业团队
  |
  v
数字办公室 GUI
  |
  v
产品后端 API
  |
  +-- 项目、用户、角色、权限、授权知识库
  +-- AI native 闭环记录
  +-- WorkflowRun、任务台、审批中心、审计日志、通知
  +-- Agent 请求、插件包、发布更新
  |
  v
Hermes Runtime
  |
  +-- scripts/agent-router
  +-- agent-system/agents.registry.json
  +-- profiles/
  +-- skills/
  +-- knowledge/company
  +-- projects/<project_id>/knowledge
  +-- KeyMemory relay
  +-- local OCR / RAG model installers
```

## AI Native 产品闭环

生产任务必须走这条闭环：

1. 感知：读取用户意图、项目、身份权限、项目知识库、公司知识库、授权行业知识、KeyMemory 接力记忆、路由候选和系统健康状态。
2. 规划：选择角色和工作流，定义交接契约、验收标准、风险、测试和回滚方案。
3. 执行：通过 `agent-router` 调度 Agent，收集产物、观察结果、交接报告和 gate 结果。
4. 反思：对照目标、证据、质量门禁和用户反馈，产出反思报告、失败原因和可复用方法论草稿。
5. 迭代：只生成用户可见的迭代提案。用户确认前，不允许静默修改规则、工作流、Agent 灵魂文档、知识库、skill 或发布配置。

相关命令：

```bash
~/.hermes/agent-system/bin/office-system loop-start --task "<task>" --project <project_id>
~/.hermes/agent-system/bin/office-system loop-stage --run-id <run_id> --stage perceive --status started
~/.hermes/agent-system/bin/office-system loop-status --run-id <run_id>

~/.hermes/agent-system/bin/office-system iteration-proposal-create --title "<title>" --target workflow --summary "<why>" --expected-impact "<impact>" --risk "<risk>" --rollback "<rollback>"
~/.hermes/agent-system/bin/office-system iteration-proposal-decision --proposal-id <proposal_id> --decision confirm
~/.hermes/agent-system/bin/office-system iteration-proposal-apply --proposal-id <proposal_id> --confirmed --regression-result "<result>"
```

## 工作流、任务台和审批中心

面向 GUI 的主入口是 `workflow-start`。它会先调用路由器判断该由哪个 Agent 或多 Agent 工作流承接，再写入可追踪的运行记录。低置信度任务不会被静默派发，而是进入秘书澄清流程。

典型用户路径：

1. 用户在 GUI 中选择项目并输入任务。
2. 系统创建 WorkflowRun 和任务台记录，写入权限决策、路由结果、审计事件和通知。
3. 如果任务需要人工确认，GUI 在审批中心展示审批项。
4. 审批通过后，任务回到队列，工作流继续执行。
5. 任务完成、失败、取消、恢复或重试都会继续写入审计和任务历史。

相关命令：

```bash
~/.hermes/agent-system/bin/office-system workflow-start --tenant <tenant_id> --deployment <deployment_id> --user <user_id> --role <role> --project <project_id> --task "<task>"
~/.hermes/agent-system/bin/office-system workflow-status --run-id <run_id>
~/.hermes/agent-system/bin/office-system workflow-list --project <project_id>
~/.hermes/agent-system/bin/office-system workflow-resume --run-id <run_id> --requested-by <user_id> --role <role>
~/.hermes/agent-system/bin/office-system workflow-retry --run-id <run_id> --stage execute --requested-by <user_id> --role <role>
~/.hermes/agent-system/bin/office-system workflow-cancel --run-id <run_id> --requested-by <user_id> --role <role> --confirmed

~/.hermes/agent-system/bin/office-system task-list --project <project_id>
~/.hermes/agent-system/bin/office-system task-status --task-id <task_id>
~/.hermes/agent-system/bin/office-system task-update --task-id <task_id> --status completed --updated-by <user_id> --role <role>

~/.hermes/agent-system/bin/office-system approval-create --tenant <tenant_id> --deployment <deployment_id> --title "<title>" --action workflow.continue --resource-type workflow_run --resource-id <run_id> --requested-by <user_id> --requested-by-role <role> --approver-role project_manager --workflow-run <run_id> --task-id <task_id>
~/.hermes/agent-system/bin/office-system approval-list --status pending
~/.hermes/agent-system/bin/office-system approval-decision --approval-id <approval_id> --decision approve --decided-by <user_id> --role <role> --confirmed

~/.hermes/agent-system/bin/office-system auth-decision --tenant <tenant_id> --deployment <deployment_id> --user <user_id> --role <role> --action workflow.start --resource-type workflow_run --resource-id <run_id> --project <project_id> --agent <agent_id>
~/.hermes/agent-system/bin/office-system audit-events --resource-type workflow_run --resource-id <run_id>
~/.hermes/agent-system/bin/office-system notification-list --user <user_id> --unread-only
```

这部分是未来数字办公室 GUI 的底座：用户看到的是“任务、审批、通知、进度和交付”，底层才是 Hermes、Agent 和命令行。

## 多 Agent 路由

核心 Agent 在 `agent-system/agents.registry.json` 中注册。

当前默认角色包括：

- `secretary`：数字办公室秘书，负责入口、澄清、路由、工作流组织、Agent 需求收集、迭代确认和 GUI 体验守护。
- `pm`：产品判断、PRD、路线图、MVP、优先级和验收标准。
- `researcher`：市场、竞品、事实、行业和假设研究。
- `planer`：架构、计划、里程碑、依赖和实施顺序。
- `vibe-designer`：GUI、UX、视觉方向、拟态化数字办公室界面和设计交付。
- `coder`：代码实现、调试、测试、重构和部署验证。
- `writer`：文章、公众号、文案、编辑和表达风格。

路由原则：

- 先选择任务需要的可迁移角色，如 `evidence`、`product`、`design`、`implementation`。
- 再通过注册表把角色映射到当前部署的 Agent。
- 不把数字律所、会计师事务所、新媒体工作室等行业版本锁死在当前 Agent 名称上。
- 低置信度或跨权限、知识库、记忆、发布、迭代的任务由秘书接管并要求澄清。

检查路由：

```bash
~/.hermes/scripts/agent-router --health
~/.hermes/scripts/agent-router --route-json "<user request>"
```

## 知识库与记忆

事实权威优先级：

1. 项目知识库
2. 公司全局知识库
3. 授权行业参考层
4. KeyMemory 接力记忆

交接优先级：

1. 当前任务状态
2. KeyMemory 项目接力
3. 项目最新决策
4. 公司全局方法论

KeyMemory 的定位：

- 适合保存项目接力摘要、子项目交接、偏好、长期操作记忆、已确认方法论摘要和检索指针。
- 不适合保存原始 PDF、Word、图片、未确认草稿、明文密钥或与项目源文件冲突的事实。

知识库命令：

```bash
~/.hermes/agent-system/bin/office-system project-create --project <project_id> --name "<name>"
~/.hermes/agent-system/bin/office-system knowledge-add --scope project --project <project_id> --file <path> --approve
~/.hermes/agent-system/bin/office-system knowledge-add-text --scope company --title "<title>" --body "<text>" --approve
~/.hermes/agent-system/bin/office-system rag-index --scope project --project <project_id>
~/.hermes/agent-system/bin/office-system rag-search --scope project --project <project_id> --query "<query>"
~/.hermes/agent-system/bin/office-system context --project <project_id> --agent <agent_id>
```

## 生产 Harness

harness 的目标是让系统真正可交付，而不是只完成原型。

它检查：

- Agent 注册表和路由健康
- 多 Agent 工作流是否按角色编排
- 设计和实现 skill 是否具备生产 gate
- AI native 闭环 manifest 是否存在
- 迭代是否强制用户确认
- 知识库、RAG、项目接力和授权知识访问是否满足契约
- 安装包能否在干净目录中跑通 smoke test

运行：

```bash
~/.hermes/agent-system/bin/harness-check
~/.hermes/agent-system/bin/harness-runner --task all --no-write
bash agent-system/tests/smoke.sh
```

## Agent 插件与企业发布

生产环境不允许客户侧秘书 Agent 自主拼装新 Agent，也不允许在 GUI 中随意增加、删除、安装或重组 skill。

新 Agent 的流程是：

1. 秘书通过对话帮助用户理清 Agent 需求。
2. 用户确认后，需求发送到我们的后端。
3. 我们设计、测试并打包 Agent 插件。
4. 企业主机下载插件包。
5. 秘书生成集成报告，说明新 Agent 如何进入现有体系和工作流。
6. GUI 显示 Confirm、Tune Through Conversation、Pause。
7. 只有 Confirm 后，系统才注册和部署新 Agent。

企业更新也应走产品发布渠道。普通用户看到的是“检查产品更新”，而不是直接更新 Hermes 或 skill。

## 本地模型

仓库不包含 OCR/RAG 模型权重。部署时按需下载：

```bash
~/.hermes/agent-system/bin/install-local-models --pack base-ocr-python
~/.hermes/agent-system/bin/install-local-models --pack base-rag-zh
```

默认策略：

- 文本、DOCX、PDF 文本提取优先本地。
- 图片 OCR 优先本地小模型或本地 OCR 工具。
- 视觉理解或低置信 OCR 才考虑经用户或管理员批准调用 VLM。

## 安装

从仓库根目录执行：

```bash
./install.sh ~/.hermes
```

安装脚本会同步 `agent-system/`、`scripts/`、`profiles/`、`skills/` 和默认 `SOUL.md`，并运行健康检查与 harness 检查。

## 仓库结构

```text
.
|-- README.md
|-- README.zh-CN.md
|-- SOUL.md
|-- install.sh
|-- scripts/
|   `-- agent-router
|-- profiles/
|-- skills/
`-- agent-system/
    |-- ai-native-loop.manifest.json
    |-- agents.registry.json
    |-- secretary.capabilities.json
    |-- knowledge.registry.json
    |-- memory.relay.registry.json
    |-- rag.pipeline.json
    |-- multimodal.pipeline.json
    |-- harness/
    |-- docs/
    |-- bin/
    |-- knowledge/
    |-- projects/
    |-- runs/
    |-- tasks/
    |-- approvals/
    |-- notifications/
    |-- logs/
    `-- rules/
```

## 设计参考

这套系统吸收了多 Agent、RAG 和生产 Agent 工程中的一些原则，但不会把外部 skill 或框架直接装进企业生产环境。

- ReAct: https://arxiv.org/abs/2210.03629
- Reflexion: https://arxiv.org/abs/2303.11366
- Generative Agents: https://arxiv.org/abs/2304.03442
- Voyager: https://arxiv.org/abs/2305.16291
- MetaGPT: https://arxiv.org/abs/2308.00352
- AutoGen: https://arxiv.org/abs/2308.08155
- SWE-bench: https://arxiv.org/abs/2310.06770
- RAGAS: https://arxiv.org/abs/2309.15217
- LangGraph durable execution: https://docs.langchain.com/oss/python/langgraph/durable-execution
- OpenHands: https://github.com/All-Hands-AI/OpenHands
- SWE-agent: https://github.com/SWE-agent/SWE-agent
- aider: https://github.com/aider-ai/aider
- 12-factor-agents: https://github.com/humanlayer/12-factor-agents
- awesome-claude-skills: https://github.com/ComposioHQ/awesome-claude-skills

## GUI 化准备更新

这次版本把底层能力整理成 GUI 可以直接调用的闭环：

- 首次打开可以通过选项定制秘书/Agent 的全局工作方式，包括语言、称呼、主动性、反驳强度、审批严格度、记忆模式和工作质量偏好。
- 使用过程中也可以在设置页继续修改这些选项。系统会保留未改动的旧选项，不会因为只改一个字段就重置全部偏好。
- `gui-state` 提供首页总览，一次返回健康状态、设置状态、Agent、项目、工作流、任务、审批、通知、知识源和审计记录。
- 工作流、任务、审批、通知和审计已经形成基础闭环：用户发起任务后，系统会生成 WorkflowRun、Task、Authorization、Audit Event 和 Notification。
- 需要用户确认的动作必须显式确认，例如取消工作流、审批决定、应用迭代方案、启用新 Agent 插件。
- 默认秘书人设改为中性基线，不再绑定个人名称或个人偏好。用户偏好保存在本地 `agent-system/settings/`，不会进入公开仓库。
- 内置专家 Profile 已去个人化，改成 Digital Office Coder、Planner、Product Manager、Researcher、Designer、Writer 等通用角色。

GUI 常用入口：

```bash
~/.hermes/agent-system/bin/office-system gui-state --user <user_id> --project <project_id>
~/.hermes/agent-system/bin/office-system onboarding-options
~/.hermes/agent-system/bin/office-system onboarding-apply --assistant-style neutral_operator --address-style neutral --language auto --initiative-level confirm_before_action --pushback-style risk_based --approval-strictness balanced --memory-mode project_only --work-mode balanced --confirmed
~/.hermes/agent-system/bin/office-system settings-status
~/.hermes/agent-system/bin/office-system settings-update --work-mode quality --confirmed
```
