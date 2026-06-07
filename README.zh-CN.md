# 数字办公室 Agent 系统

这是一套基于 Hermes 的数字办公室底层实验系统。它的目标不是直接暴露 Hermes 命令行，而是把 Hermes 包装成一个未来可迁移、可产品化、可接入 GUI 的数字办公室运行层。

当前仓库重点覆盖：

- 多 Agent 注册、路由和工作流编排
- 公司全局知识库、项目知识库、授权行业参考层和 KeyMemory 之间的协作
- 本地多模态文档处理与 RAG 能力预留
- 企业部署、产品更新、Agent 插件包和行业方案库预留
- 面向未来 GUI 的命令契约
- 多人类用户、Agent 员工、项目权限和知识库调用审计预留

## 产品边界

生产环境里，客户看到的是数字办公室 GUI，不是 Hermes 原始命令行。

Hermes 应该作为底层运行时存在，负责 Agent 执行、路由、技能调用和本地知识处理。客户侧的新 Agent、技能组合、行业方案、产品更新，都应该通过我们验证后的发布渠道进入企业部署环境。

一个重要原则：

> 客户使用数字办公室；开发者维护 Hermes 运行层；我们通过后端控制行业方案、Agent 插件、授权知识库和产品版本。

## 系统分层

当前设计可以理解成十层：

1. 数字办公室 GUI
2. 产品后端 API
3. 企业租户、用户、角色、席位和授权控制
4. Hermes 运行时
5. `agent-system` 注册表和策略
6. Agent profile 与 skill
7. 公司全局知识库和项目知识库
8. 授权行业参考层
9. KeyMemory 接力记忆和语义记忆
10. 本地 OCR、文档解析和 RAG 模型能力

对应设计文档：

- [架构设计](agent-system/docs/architecture.md)
- [GUI 契约](agent-system/docs/gui-contract.md)
- [行业知识库与连接器](agent-system/docs/industry-knowledge-and-connectors.md)
- [企业发布设计](agent-system/docs/enterprise-release-design.md)
- [数据共享设计](agent-system/docs/data-sharing-design.md)
- [本地模型设计](agent-system/docs/local-models.md)

## 快速安装

从仓库根目录执行：

```bash
./install.sh ~/.hermes
```

安装脚本会把 `agent-system/`、`scripts/`、`profiles/`、`skills/` 和默认 `SOUL.md` 安装到目标 Hermes 目录。

如果目标目录已经存在 `SOUL.md`，安装脚本会先备份：

```text
SOUL.before-digital-office.<timestamp>.md
```

## 健康检查

安装后可以运行：

```bash
~/.hermes/scripts/agent-router --health
~/.hermes/agent-system/bin/office-system health
~/.hermes/agent-system/bin/harness-check
~/.hermes/agent-system/bin/product-update status
```

本地 OCR 和 RAG 模型权重不会提交到 GitHub。部署时由客户主机下载：

```bash
~/.hermes/agent-system/bin/install-local-models --pack base-ocr-python
~/.hermes/agent-system/bin/install-local-models --pack base-rag-zh
```

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
    |-- agents.registry.json
    |-- knowledge.registry.json
    |-- identity.access.registry.json
    |-- industry-solutions.registry.json
    |-- external-knowledge-sources.registry.json
    |-- memory.relay.registry.json
    |-- product.release.manifest.json
    |-- release.policy.json
    |-- multimodal.pipeline.json
    |-- rag.pipeline.json
    |-- models.local.manifest.json
    |-- bin/
    |-- docs/
    |-- knowledge/
    |-- projects/
    `-- rules/
```

## Agent 与路由

Agent 队伍由 [agents.registry.json](agent-system/agents.registry.json) 管理。

当前注册的核心 Agent 包括：

- `secretary`：数字办公室秘书，负责需求入口、任务组织、Agent 需求澄清和部署报告
- `pm`：产品经理
- `researcher`：研究员
- `planer`：规划师
- `vibe-designer`：设计师
- `coder`：工程实现
- `writer`：写作与内容

路由器是 [scripts/agent-router](scripts/agent-router)。它只读取注册表，不把 Agent、模型和工作流写死在脚本里。

开发者新增 Agent 时，应该优先扩展注册表，而不是修改路由器逻辑。

## 知识库与记忆

系统里有四类上下文来源：

1. 项目知识库
2. 公司全局知识库
3. 授权行业参考层
4. KeyMemory

事实优先级：

```text
项目知识库 > 公司全局知识库 > 授权行业参考层 > KeyMemory
```

KeyMemory 适合做项目接力、偏好、跨 Agent 连续性、方法论摘要和语义指针，但不应该保存原始 PDF、Word、图片、未审批项目草稿或我们销售的行业知识库源文件。

## 在线知识库注入规则

外部知识源分两类。

客户自有知识源：

- 可以挂载到公司全局知识库
- 可以挂载到项目知识库
- 可以挂载到特定 Agent 的专业上下文

例如 ima、Notion、腾讯文档、得到笔记、AI 录音卡片、飞书文档、本地 NAS 文档等。

我们销售的行业知识库：

- 只能作为授权行业参考层挂载
- 不允许写入客户的公司库或项目库原文目录
- 不允许下载、导出、批量复制、外部 API 调用或暴露源文件路径
- 每次调用都必须记录企业、部署、用户、角色、项目、Agent、工作流、知识包、授权和调用结果

相关注册表：

- [industry-solutions.registry.json](agent-system/industry-solutions.registry.json)
- [external-knowledge-sources.registry.json](agent-system/external-knowledge-sources.registry.json)
- [identity.access.registry.json](agent-system/identity.access.registry.json)

## GUI 后端契约

`office-system` 是当前给未来 GUI 和产品后端调用的控制命令。

常用命令：

```bash
~/.hermes/agent-system/bin/office-system project-create --project <project_id> --name "<name>"
~/.hermes/agent-system/bin/office-system context --project <project_id> --agent <agent_id>
~/.hermes/agent-system/bin/office-system knowledge-add --scope project --project <project_id> --file <path>
~/.hermes/agent-system/bin/office-system rag-index --scope project --project <project_id>
~/.hermes/agent-system/bin/office-system rag-search --scope project --project <project_id> --query "<query>"
```

多人和授权知识库相关命令：

```bash
~/.hermes/agent-system/bin/office-system identity-context --tenant <tenant_id> --deployment <deployment_id> --user <user_id> --role <role>
~/.hermes/agent-system/bin/office-system knowledge-source-mount --source-class provider_sold_industry_kb --source-id <pack_id> --tenant <tenant_id> --deployment <deployment_id> --created-by <user_id> --mount-target licensed_project_reference --project <project_id> --entitlement <entitlement_id>
~/.hermes/agent-system/bin/office-system knowledge-access-log --tenant <tenant_id> --deployment <deployment_id> --user <user_id> --role <role> --source-class provider_sold_industry_kb --source-id <pack_id> --mount-id <mount_id> --decision allow
```

完整契约见 [GUI 契约](agent-system/docs/gui-contract.md)。

## 多人使用预留

当前实验可以单人使用，但产品设计必须支持真实团队。

系统区分三类身份：

- `human_user`：真实人类用户
- `agent_worker`：Agent 员工
- `support_operator`：我们自己的支持或交付人员

未来 GUI 应至少提供：

- 团队成员
- 角色与权限
- 项目成员
- Agent 委派
- 知识访问日志
- 席位与授权用量
- 支持访问开关

人类用户能否启动工作流、审批专业结论、使用某个付费行业知识库，都应该由身份、角色、项目成员关系和授权共同决定。

## 行业方案与 Agent 插件

行业方案库不是普通模板库，而是未来可销售、可授权、可更新的产品资产。

建议把行业方案做成 package：

```text
industry_solutions/<solution_id>/
|-- manifest.json
|-- workflows/
|-- agents/
|-- rules/
|-- knowledge_templates/
|-- gui/
`-- evals/
```

新 Agent 的生产路径：

1. 秘书 Agent 与客户对话，澄清需求
2. 用户确认需求
3. 需求提交到我们的产品后端
4. 我们设计、测试并发布 Agent 插件包
5. 企业本地下载插件包
6. 秘书 Agent 生成部署报告
7. 用户确认、微调或暂不处理
8. 只有确认后的报告 ID 才能用于注册和部署 Agent

客户可以通过对话改进已有 Agent 的 SOUL 或工作流，但不允许在生产环境里自行增删、安装、替换或重组 skill。

## 本地多模态和 RAG

当前设计是本地优先：

- 文本和 Markdown：本地解析
- Word：本地 DOCX 抽取
- PDF：`pdftotext` 或 `pypdf`
- 图片 OCR：Tesseract 或 RapidOCR
- RAG embedding：本地 sentence-transformer 模型

视觉大模型只作为低置信度 OCR 或复杂视觉理解的 fallback。

模型权重不进入 GitHub 仓库，部署时按 manifest 下载。

## 数据共享边界

允许默认共享的内容应该尽量是低风险运行数据：

- 路由和工作流统计，不含原始 prompt
- 健康状态
- 模型能力状态
- 经用户审批的方法论摘要
- 脱敏后的项目接力模式

默认禁止：

- 原始公司文档
- 原始项目文档
- 原始图片
- 未审批草稿
- 原始 KeyMemory 记录
- 凭证和密钥

企业管理员必须可以审核导出内容，也必须可以关闭共享。

## 开发检查清单

修改前先确认：

- 是否应该改注册表，而不是改脚本逻辑
- 是否会破坏 `secretary` 使用默认 `SOUL.md` 的约定
- 是否把客户数据、日志、模型权重或密钥加入 Git
- 是否为未来 GUI 保留了命令契约或配置入口
- 是否保留了迁移到数字律所、数字会计师事务所、数字新媒体工作室的可迁移性

提交前建议运行：

```bash
python3 -m json.tool agent-system/agents.registry.json >/dev/null
python3 -m json.tool agent-system/knowledge.registry.json >/dev/null
python3 -m json.tool agent-system/identity.access.registry.json >/dev/null
python3 -m py_compile agent-system/bin/office-system.py
agent-system/bin/office-system health
scripts/agent-router --health
git diff --check
```

## 开发原则

1. GUI 优先，不暴露 Hermes 内部复杂度。
2. 注册表优先，避免把业务规则写死在脚本里。
3. 项目优先，Agent、知识库、规则和工作流都围绕项目展开。
4. 权限优先，尤其是授权行业知识库和多人团队使用。
5. 本地优先，企业原始资料默认留在客户主机。
6. 可迁移优先，行业包、Agent 插件、知识产品和 GUI 后端应能拆分演进。

## 当前状态

这是一个底层实验与产品化骨架，不是完整商业产品。

它已经预留了：

- Agent 注册与路由
- 项目和知识库目录结构
- 本地 OCR/RAG 能力
- KeyMemory 接力层
- 新 Agent 插件流程
- 企业发布与回滚
- 行业方案库和授权知识库
- 第三方知识库连接器
- 多人身份与权限审计

下一步应该优先补：

- GUI 项目工作台
- 预设工作流包
- 产品后端控制平面
- 行业方案包格式和发布流程
- 真实连接器实现
- 工作流执行状态机
- 回归测试和评测集
