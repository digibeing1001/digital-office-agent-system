# 数字办公室 Agent System

数字办公室 Agent System 是一套可分发的多 Agent 办公运行层。它可以部署到 Hermes、OpenClaw 或其他兼容 Agent 宿主中，把宿主默认 Agent 注入为“数字办公室秘书”，再由秘书统一完成需求收口、角色路由、工作流编排、知识边界、质量门禁和交付说明。

这不是个人本地规则集合，也不是单纯的命令行配置包。产品目标是让用户或团队在 GUI 中创建项目、上传知识、分派任务、查看 Agent 协作、确认迭代并接收交付；底层宿主负责执行，数字办公室套件负责把执行组织成可验证、可回滚、可持续更新的产品工作流。

## 产品定位

- 面向用户：提供一个可操作的数字办公室，而不是要求用户理解底层 Agent 工具。
- 面向部署管理员：提供安装、注入、备份、验证和回滚路径，保护原宿主中的个人规则和数据。
- 面向开发者：提供注册表、规则、技能来源、质量门禁和发布清单，确保每次更新都能进入可分发版本。

当前仓库是 internal 开发通道。生产客户应接收经过验证的数字办公室发布包，而不是直接拉取上游宿主、随意安装 skill 或手动覆盖本地规则。

## 核心能力

- 多 Agent 办公室：秘书、PM、研究员、规划师、设计师、工程师、Writer 等数字员工通过统一注册表协作。
- 默认 Agent 秘书注入：安装后宿主默认 Agent 承担秘书职责，不再沿用宿主原始默认规则作为最高优先级。
- 可迁移路由：`scripts/agent-router` 先选择 portable role，再映射到当前部署中的具体 Agent，避免把产品逻辑锁死在某个宿主或 Agent 名称上。
- 工作流控制面：任务启动时同步创建 WorkflowRun、任务记录、权限决策、审计事件和通知。
- 质量门禁：`harness-check` 与 `harness-runner` 验证路由、工作流、知识权限、GUI 合约、PWA、AI native loop、设计/编码生产门禁、PPT 生产和宿主注入策略。
- 知识与记忆边界：项目知识、公司知识、授权行业参考层和 KeyMemory 接力记忆分层管理，避免把个人偏好或未确认草稿当作事实源。
- 产品化更新：普通用户看到的是数字办公室产品更新，不需要直接管理 Hermes、OpenClaw、skill 或底层模型。

## 支持宿主

| 宿主 | 默认目标目录 | 注入入口 | 默认 Agent 角色 |
| --- | --- | --- | --- |
| Hermes | `~/.hermes` | `SOUL.md` | `secretary` |
| OpenClaw | `~/.openclaw` | `AGENTS.md` | `secretary` |
| generic | `~/.digital-office-agent` | `AGENTS.md` | `secretary` |

宿主注入策略的机器可读来源是 `agent-system/host-injection.policy.json`。中文说明见 [agent-system/docs/host-rule-injection.zh-CN.md](agent-system/docs/host-rule-injection.zh-CN.md)。

## 安装与注入

从仓库根目录执行：

```bash
./install.sh --host hermes --target ~/.hermes
./install.sh --host openclaw --target ~/.openclaw
```

干净宿主会自动注入数字办公室默认 Agent 入口，并同步 `agent-system/`、`scripts/`、`profiles/`、`skills/`、README 和产品文档。

如果目标宿主已有个人规则、用户偏好、项目、知识、任务或运行记录，安装器不会静默覆盖。管理员必须明确选择：

```bash
# 保留原宿主规则和个人数据，把数字办公室旁路安装到 digital-office/
./install.sh --host openclaw --target ~/.openclaw --preserve-existing

# 备份原入口文件，然后用数字办公室秘书入口覆盖默认 Agent 入口
./install.sh --host openclaw --target ~/.openclaw --overwrite-existing
```

安装器默认运行：

```bash
scripts/agent-router --health
agent-system/bin/office-system health
agent-system/bin/harness-check
agent-system/bin/harness-runner --task all --no-write
agent-system/bin/product-update status
```

## 默认秘书 Agent

默认宿主 Agent 被注入为数字办公室秘书 Agent。秘书负责：

1. 澄清用户意图、项目、受众、权限和验收标准。
2. 通过 `agents.registry.json` 选择 portable role 和具体 Agent。
3. 管理多 Agent 交接，确保后续角色使用前序产物，而不是重头开始。
4. 使用 `production-gates.json` 和相关 harness 任务检查质量。
5. 给出最终交付说明，包括文件路径、URL、打开方式、风险和未解决假设。

默认秘书人设改为中性基线。用户偏好通过 GUI onboarding 和设置文件表达，不能覆盖安全、权限、知识来源、生产门禁或发布控制。

## 典型工作流

### PPT 生产

PPT、slides、deck、presentation、汇报、幻灯片等需求会进入 `ppt_production`：

```text
intake -> writing -> design -> intake
```

- 秘书 `intake`：澄清目标、受众、页数、素材、交付格式和验收标准。
- Writer `writing`：负责故事线、页面文案、标题层级、讲稿和事实表述。
- Designer `design`：负责视觉方向、版式、媒体决策和可渲染 deck artifact。
- 秘书 `intake`：执行最终门禁，交付文件路径、URL 或打开方式，并说明未解决假设。

Writer 不承担最终 HTML/PPT deck 渲染，除非未来显式注册了 deck 渲染技能并通过同等门禁。

### Vibe Design / Vibe Coding

设计和编码类任务分别使用 `vibe-design-production-harness` 与 `vibe-coding-production-harness`。工作流必须保留产品判断、设计方向、实现验证和回归检查，不允许把生产门禁压缩成“看起来完成了”。

### AI Native Product Loop

生产任务遵循：

```text
Perceive -> Plan -> Execute -> Reflect -> Iterate
```

迭代必须生成用户可见提案。用户确认前，不允许静默修改规则、工作流、Agent 行为、知识库、skill bundle、模型路由、GUI 合约或发布配置。

## GUI 化准备更新

GUI 的入口命令由 `agent-system/bin/office-system` 提供。当前产品层已经具备以下后端契约：

```bash
agent-system/bin/office-system gui-state --user <user_id> --project <project_id>
agent-system/bin/office-system onboarding-options
agent-system/bin/office-system onboarding-apply --assistant-style neutral_operator --address-style neutral --language auto --initiative-level confirm_before_action --pushback-style risk_based --approval-strictness balanced --memory-mode project_only --work-mode balanced --confirmed
agent-system/bin/office-system settings-status
agent-system/bin/office-system settings-update --work-mode quality --confirmed
```

`gui-state` 返回健康状态、设置、能力、Agent、项目、工作流、任务、审批、通知、知识和审计摘要。`settings-update` 用于 GUI 的局部设置更新。普通用户不应直接编辑宿主规则文件。

## Web UI And PWA

仓库包含一个可安装的 Web/PWA shell，用于未来 GUI 迭代。管理员可以配置和启动本地 Web UI：

```bash
agent-system/bin/office-system web-config --public-url https://office.example.com
agent-system/bin/office-system web-serve --host 127.0.0.1 --port 8787 --public-url https://office.example.com
```

浏览器访问本地服务后可选择 Install as PWA。对外暴露时应使用 HTTPS，否则 PWA 安装能力和浏览器权限会受限。

## 验证与开发

本仓库以可分发产品版本为开发目标。每次更新都应确认：

1. 安装包能在用户主机上完成安装、规则注入和健康检查。
2. 关键工作流能闭环交付，不停留在文档或手动操作。
3. `harness-check` 和相关 `harness-runner` 任务通过。
4. 中文 README 面向用户、部署管理员和开发者，不写成个人运行记录。
5. WSL Hermes 开发目录与 GitHub 仓库保持同步。

常用检查：

```bash
python3 -m py_compile agent-system/bin/office-system.py agent-system/bin/harness-check agent-system/bin/harness-runner scripts/agent-router
agent-system/bin/harness-check
agent-system/bin/harness-runner --task all --no-write
bash agent-system/tests/smoke.sh
```

查看路由：

```bash
scripts/agent-router --health
scripts/agent-router --route-json "帮我做一份PPT汇报"
scripts/agent-router --route-json "research competitors, decide product requirements, design the interface, then implement the code"
```

## 仓库结构

```text
.
|-- install.sh
|-- SOUL.md
|-- README.md
|-- README.zh-CN.md
|-- scripts/
|   `-- agent-router
|-- profiles/
|-- skills/
`-- agent-system/
    |-- agents.registry.json
    |-- secretary.capabilities.json
    |-- host-injection.policy.json
    |-- product.release.manifest.json
    |-- harness/
    |-- docs/
    |-- bin/
    |-- rules/
    |-- knowledge/
    |-- projects/
    |-- tasks/
    `-- runs/
```

## 关键文档

- [agent-system/docs/architecture.md](agent-system/docs/architecture.md)：总体架构、宿主注入、规则优先级、知识和发布模型。
- [agent-system/docs/host-rule-injection.zh-CN.md](agent-system/docs/host-rule-injection.zh-CN.md)：Hermes、OpenClaw 和 generic 宿主注入策略。
- [agent-system/docs/ppt-production-workflow.md](agent-system/docs/ppt-production-workflow.md)：PPT 生产工作流和角色边界。
- [agent-system/docs/production-harness.md](agent-system/docs/production-harness.md)：生产门禁设计。
- [agent-system/docs/gui-contract.md](agent-system/docs/gui-contract.md)：未来 GUI 与本地运行层的命令合约。

## 产品开发更新日志

### 2026-06-09

- 新增 `ppt_production` 工作流，顺序为 `intake -> writing -> design -> intake`。
- 新增 PPT 外部技能来源登记：`humanize-ppt`、`huashu-design`、`guizang-ppt-skill`、`frontend-slides`；`pitch-clarity-coach` 保持 research-only，不作为生产秘书技能启用。
- 新增宿主注入策略，支持 Hermes、OpenClaw 和 generic 宿主。
- 安装器新增 `--host`、`--overwrite-existing`、`--preserve-existing`、`--no-check` 选项。
- 默认宿主 Agent 明确注入为数字办公室秘书 Agent。
- 主 README 与中文 README 调整为面向用户、部署管理员和开发者的产品说明与开发更新日志。
