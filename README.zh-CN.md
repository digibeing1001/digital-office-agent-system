# 数字办公室 Agent System 中文说明

主 README 见 [README.md](README.md)。本文件面向用户、部署管理员和开发者，说明数字办公室套件的产品能力、安装方式、验证方式和开发更新记录。内容应保持产品化，不记录个人运行时偏好。

## 产品开发更新日志

### 2026-06-09

- 新增 PPT 生产工作流：`intake -> writing -> design -> intake`。秘书负责需求收口和最终交付，Writer 负责故事线、页面文案和讲稿，Designer 负责视觉方向和可渲染 deck artifact。
- 新增 Hermes、OpenClaw 和 generic 宿主注入策略。干净宿主默认注入数字办公室规则；已有个人规则或数据的宿主必须选择并行保留或显式覆盖。
- 默认宿主 Agent 被注入为数字办公室秘书 Agent，负责路由、工作流编排、交接、质量门禁和交付说明。
- 每次产品更新都应同步到 WSL Hermes 开发目录并上传 GitHub，以可分发版本质量为目标进行 review。

宿主规则注入细节见 [host-rule-injection.zh-CN.md](agent-system/docs/host-rule-injection.zh-CN.md)。

## 这套系统是什么

它是一套面向 GUI 数字办公室产品的 Hermes 运行层，核心是：

- 多 Agent 注册、路由和工作流编排
- 公司全局知识库、项目知识库、授权行业参考层和 KeyMemory 接力记忆
- 本地多模态文档处理和 RAG 能力
- AI native 产品闭环：感知、规划、执行、反思及迭代
- 面向 GUI 的 WorkflowRun、任务台、审批中心、权限决策、审计日志和通知
- 用户确认式迭代，不允许黑盒自我修改
- 企业发布、Agent 插件包、行业知识库和权限审计预留

## 开发原则

1. 不把当前 Agent 名称写死到产品逻辑里。先使用 portable role，再从 `agents.registry.json` 解析到具体 Agent。
2. 不让 KeyMemory 取代项目知识库或公司知识库。KeyMemory 是接力和语义记忆层，不是事实源。
3. 不允许客户生产环境自行拼装 skill。新 Agent 能力通过我们验证后的 Agent 插件包交付。
4. 不允许系统静默自我迭代。任何规则、工作流、Agent 行为、知识方法论、harness 或发布配置的改进，都必须先生成迭代提案，让用户确认。
5. 不把 OCR/RAG 模型权重提交到仓库。部署时由 `install-local-models` 下载到客户主机。
6. 所有新增后端能力都必须有 GUI 契约，不能只提供 CLI。

## 关键文件

```text
SOUL.md                                      默认秘书 Agent 入口
scripts/agent-router                        智能路由器
agent-system/agents.registry.json           Agent 注册表
agent-system/secretary.capabilities.json    秘书能力和策略
agent-system/ai-native-loop.manifest.json   AI native 闭环定义
agent-system/knowledge.registry.json        知识库与记忆优先级
agent-system/memory.relay.registry.json     KeyMemory 接力规则
agent-system/rag.pipeline.json              本地 RAG 管线
agent-system/multimodal.pipeline.json       多模态解析管线
agent-system/harness/production-gates.json  生产门禁
agent-system/harness/tasks/*.json           可执行 harness 任务
agent-system/bin/office-system.py           GUI 后端控制面
agent-system/docs/gui-contract.md           GUI 契约
agent-system/docs/production-harness.md     生产 harness 设计
agent-system/runs/                          WorkflowRun 运行态记录
agent-system/tasks/                         任务台运行态记录
agent-system/approvals/                     审批中心运行态记录
agent-system/notifications/                 GUI 通知运行态记录
agent-system/logs/                          审计和系统日志
```

## AI Native 闭环开发契约

闭环定义在 `agent-system/ai-native-loop.manifest.json`。

阶段：

1. `perceive`：感知用户意图、项目、权限、知识、记忆和路由候选。
2. `plan`：规划角色、工作流、交接、验收、风险、测试和回滚。
3. `execute`：通过 router 调用 Agent，记录产物、观察和 gate。
4. `reflect`：对照计划和证据进行反思，形成问题、复用方法和改进建议。
5. `iterate`：生成用户可见的迭代提案，等待用户确认后才应用。

新增闭环相关能力时，应同步更新：

- `agent-system/ai-native-loop.manifest.json`
- `agent-system/docs/gui-contract.md`
- `agent-system/harness/tasks/ai-native-loop-production.json`
- `agent-system/harness/tasks/workflow-control-plane-production.json`
- `agent-system/tests/smoke.sh`

## 常用命令

安装到 Hermes：

```bash
./install.sh ~/.hermes
```

健康检查：

```bash
~/.hermes/scripts/agent-router --health
~/.hermes/agent-system/bin/office-system health
~/.hermes/agent-system/bin/harness-check
~/.hermes/agent-system/bin/harness-runner --task all --no-write
```

创建项目和知识：

```bash
~/.hermes/agent-system/bin/office-system project-create --project p1 --name "Project One" --agents pm,coder
~/.hermes/agent-system/bin/office-system knowledge-add-text --scope project --project p1 --title "Brief" --body "..." --approve
~/.hermes/agent-system/bin/office-system rag-index --scope project --project p1
~/.hermes/agent-system/bin/office-system context --project p1 --agent pm
```

AI native 闭环：

```bash
~/.hermes/agent-system/bin/office-system loop-start --task "..." --project p1
~/.hermes/agent-system/bin/office-system loop-stage --run-id <run_id> --stage perceive --status started
~/.hermes/agent-system/bin/office-system loop-status --run-id <run_id>
```

GUI 工作流控制面：

```bash
~/.hermes/agent-system/bin/office-system workflow-start --tenant t1 --deployment d1 --user u1 --role project_manager --project p1 --task "product requirement design ui prototype code implement frontend"
~/.hermes/agent-system/bin/office-system task-list --project p1
~/.hermes/agent-system/bin/office-system approval-list --status pending
~/.hermes/agent-system/bin/office-system audit-events --resource-type workflow_run --resource-id <run_id>
~/.hermes/agent-system/bin/office-system notification-list --user u1 --unread-only
```

迭代提案：

```bash
~/.hermes/agent-system/bin/office-system iteration-proposal-create --title "..." --target workflow --summary "..." --expected-impact "..." --risk "..." --rollback "..."
~/.hermes/agent-system/bin/office-system iteration-proposal-decision --proposal-id <proposal_id> --decision confirm
~/.hermes/agent-system/bin/office-system iteration-proposal-apply --proposal-id <proposal_id> --confirmed --regression-result "harness passed"
```

## 测试与 Review

提交前至少运行：

```bash
python3 -m py_compile agent-system/bin/office-system.py agent-system/bin/harness-check agent-system/bin/harness-runner scripts/agent-router
./agent-system/bin/harness-check
./agent-system/bin/harness-runner --task all --no-write
bash agent-system/tests/smoke.sh
git diff --check
```

生产交付前还要做人工 review：

- README 和 GUI 契约是否与实际命令一致
- `workflow-control-plane-production` 是否覆盖 WorkflowRun、任务台、审批、权限、审计和通知闭环
- router 是否仍然基于角色而不是硬编码 Agent
- 迭代是否强制用户确认
- 知识库优先级是否没有被 KeyMemory 或授权参考层覆盖
- harness 任务是否能在干净安装目录跑通

## 参考

本系统主要吸收以下方向的工程原则：

- ReAct: action / observation loop
- Reflexion: reflective feedback
- Generative Agents: memory / reflection / planning separation
- Voyager: reviewed reusable skill library
- MetaGPT and AutoGen: role-based multi-Agent collaboration
- LangGraph: durable execution and human-in-the-loop state
- SWE-agent, SWE-bench, aider, OpenHands: coding-agent harness and deterministic evaluation
- RAGAS, Self-RAG, CRAG: retrieval quality and critique

## GUI 化准备更新

这一版的重点是让未来 GUI 可以完整使用底层系统，而不是只把 CLI 包一层外壳：

- 首次打开 GUI 时，用户可以通过选项配置秘书/Agent 的全局工作方式：语言、称呼、主动性、反驳强度、审批严格度、记忆模式和工作质量偏好。
- 后续使用过程中，用户也可以在设置页继续修改这些选项；`settings-update` 支持局部更新，未提交字段会沿用旧值。
- `gui-state` 是 GUI 首页总览接口，一次返回健康状态、设置、Agent、项目、工作流、任务、审批、通知、知识源和审计记录。
- 工作流控制面已经把 WorkflowRun、Task、Authorization、Audit Event、Notification 串成闭环。
- 需要用户确认的动作必须经过 GUI 显式确认，例如取消工作流、审批决定、应用迭代方案、启用 Agent 插件。
- 默认秘书改成中性基线，不再绑定个人名称或个人偏好；用户偏好保存在本地 `agent-system/settings/`，不会进入公开仓库。
- 内置专家 Profile 已去个人化，改为 Digital Office Coder、Planner、Product Manager、Researcher、Designer、Writer 等通用角色。

GUI 常用入口：

```bash
~/.hermes/agent-system/bin/office-system gui-state --user <user_id> --project <project_id>
~/.hermes/agent-system/bin/office-system onboarding-options
~/.hermes/agent-system/bin/office-system onboarding-apply --assistant-style neutral_operator --address-style neutral --language auto --initiative-level confirm_before_action --pushback-style risk_based --approval-strictness balanced --memory-mode project_only --work-mode balanced --confirmed
~/.hermes/agent-system/bin/office-system settings-status
~/.hermes/agent-system/bin/office-system settings-update --work-mode quality --confirmed
```

外部 skill 和高星项目只能作为候选来源。企业生产中必须经过 staged review、许可和安全检查、适配、harness 验证、管理员确认后才可启用。

## GUI Backplane Update

This version reserves the backend needed for the future GUI before drawing the actual screens.

- `agent-invoke` lets the GUI support direct `@Agent` calls without bypassing governance.
- Workflow canvas edits use draft revisions, validation, and confirmed activation.
- `workflow-control` supports run, pause, resume, and stop. Stop requires confirmation.
- Canvas components are constrained to known office workflow types instead of arbitrary low-code blocks.
- Knowledge spaces now support personal, project, team, company, workflow artifact, and shared-with-me views.
- Personal folders are private by default. Sharing can target users, roles, Agents, projects, or workflow scopes.
- `knowledge-scope-resolve` defaults to snapshot mode for reproducible workflow runs.
- `workbench-state` returns role-specific dashboards for owners, project leads, members, approvers, and viewers.

New production harness tasks:

```bash
~/.hermes/agent-system/bin/harness-runner --task direct-agent-invocation-production --no-write
~/.hermes/agent-system/bin/harness-runner --task workflow-canvas-revision-production --no-write
~/.hermes/agent-system/bin/harness-runner --task knowledge-space-acl-production --no-write
~/.hermes/agent-system/bin/harness-runner --task role-workbench-production --no-write
```

## Web UI And PWA Developer Contract

The first commercial GUI target is Web UI plus PWA, not a wrapped browser client. The backend now exposes the stable shell and read-only browser API needed by the later frontend.

```bash
~/.hermes/agent-system/bin/office-system web-config --public-url https://office.example.com
~/.hermes/agent-system/bin/office-system web-serve --host 127.0.0.1 --port 8787 --public-url https://office.example.com --quiet
```

Frontend developers should use these routes:

- `GET /api/health`
- `GET /api/gui-state`
- `GET /api/web-app`
- `/manifest.webmanifest`
- `/service-worker.js`

Deployment templates:

- `agent-system/deploy/Caddyfile.example`
- `agent-system/deploy/nginx.conf.example`
- `agent-system/deploy/systemd/digital-office-web.service.example`

Rules:

- Use HTTPS when exposing the app outside localhost, otherwise PWA install will not be reliable.
- Bind `web-serve` to `127.0.0.1` behind reverse proxy for internet-facing deployments.
- Use `--host 0.0.0.0` only on trusted LAN/VPN networks.
- Do not add a generic remote shell or arbitrary CLI executor to the Web UI. Mutations must use governed backend commands or dedicated API routes with audit and confirmation.
- Keep `web-pwa-production` and `agent-system/tests/web-pwa-smoke.sh` passing before building the visual GUI on top of this layer.
