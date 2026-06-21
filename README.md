# Digital Office 数字办公室

Digital Office 是一套可以装进 Hermes、OpenClaw 或其他 Agent 主机的“数字办公室”。

你只需要把事情告诉秘书 Agent。秘书会判断该找谁、要不要先问清楚、哪些步骤需要审批，再把工作交给合适的数字员工。写作、研究、产品、设计、开发、规划和企业法务都有各自的数字员工；它们下面不再堆更多 Agent，而是调用一组经过约束的 Skill 完成工作。

当前版本已经完成一版可运行 GUI，并把产品分成两个清楚的入口：普通用户使用“我的办公室”查看全局看板，通过秘书创建项目、上传资料、推进项目对话，并在“数字员工”里查看每个 Agent 的能力和真实调用表现；管理员使用“管理中心”维护 Agent、Skill、运行状态、策略和审计。两套界面共用同一套受控后端，不会各自保存一套互相打架的业务状态。

## 一分钟理解

可以把它理解成：

```text
你
└── 秘书 Agent：接任务、澄清、分派、盯进度、管审批
    ├── 研究员 Agent ── 检索、证据、引用等 Skills
    ├── 产品经理 Agent ── 需求、优先级、验收等 Skills
    ├── 设计师 Agent ── 交互、视觉、原型、无障碍等 Skills
    ├── 程序员 Agent ── 编码、调试、测试、部署等 Skills
    ├── 写作 Agent ── 提纲、起草、编辑等 Skills
    ├── 规划 Agent ── 架构、里程碑、依赖、风险等 Skills
    └── 数字律师 Agent ── 合同、合规、隐私、公司法等 Skills
```

Agent 是对结果负责的数字员工，Skill 是它内部使用的专业能力。部门可以作为用户理解业务边界的方式，但系统不会模拟一棵层层汇报的人类组织树。

## 它解决什么问题

普通多 Agent 系统常见的问题不是“Agent 不够多”，而是任务一转手，目标、证据、限制和已经做过的决定就开始丢。

Digital Office 把重点放在四件事上：

1. **工作有负责人**：秘书负责入口，每项专业工作只交给一个明确的数字员工 Agent。
2. **交接不靠聊天记忆**：任务用带版本、来源、风险、产物引用和哈希的交接包传递，接收方必须确认收到。
3. **任务不会无限循环**：每次工作都有循环次数、重试、时间、工具调用和模型调用上限。
4. **高风险动作有人把关**：法务、外部发送、上线、签署等动作可以被审批或专业判断门拦住。

## 和常见方案相比

| 常见做法 | Digital Office 的做法 |
| --- | --- |
| 为每个小步骤再建一个 Agent | 一个数字员工 Agent 负责一个方向，小步骤交给 Skills |
| 把整段聊天转给下一个 Agent | 只传最小必要上下文，大文件和证据按引用取回 |
| 让模型自己决定是否继续循环 | 后端控制器决定继续、重做、等待人工、完成或失败 |
| 成功与否主要看模型说“完成了” | 必须经过验收条件、产物、门禁和可回放账本 |
| 更新程序时顺便覆盖本地数据 | 程序文件与项目、知识、任务、偏好、认证数据分开 |
| 法务能力等同于一个万能律师提示词 | 企业内设数字律师，按合同、隐私、合规等 Skill 通道工作，并保留人工复核 |

这并不意味着它比所有 Agent 产品都更聪明。它的优势是更容易知道任务现在在哪里、为什么停住、交接时带了什么、出了问题如何恢复。

## 已经具备的能力

- 秘书 Agent 统一接收、澄清和分派任务
- 研究、产品、设计、开发、写作、规划、企业法务等数字员工
- `Context -> Decide -> Act -> Evaluate` 四节点工作循环
- 继续、改计划、重试、等待人工、完成、失败、取消和预算耗尽等明确状态
- 可恢复检查点、并发安全的哈希链账本、备份和原子恢复
- 带来源、事实置信度、省略说明、权限和接收确认的上下文交接
- 项目知识、公司知识、文件夹权限、审批、通知和审计记录
- 企业数字律师常用工作流和本地法律 Skill 包
- 可安装为 PWA 的用户端与管理后台
- 用户可通过秘书创建项目、在项目内发起对话、上传项目资料和查看交付记录
- 新项目先由秘书复述用户意图，再用至少三道第一性原理问题补齐目标、交付物、验收标准、边界和事实依据；用户确认当前版本后才允许执行
- 项目底稿带版本和哈希，核心目标被修改后旧确认自动失效；上下文不足或可能偏离时会暂停在检查点并提示需要补充什么
- 数字员工页面可查看每个 Agent 的介绍、能力、调用次数、Token 消耗、成功失败和系统建议补齐的岗位
- 管理员可创建、停用、归档和删除自定义 Agent
- 健康检查、权限控制、审计记录和专用 Web 操作接口
- 同时支持已安装的 Agent 主机与模型 API；内置 MiniMax、MiMo、Kimi、智谱 GLM、OpenAI、Anthropic、Gemini 和自定义兼容服务
- API Key 与 Token Plan 分开管理，可自行填写 API 地址、模型和密钥，并设置本地优先或 API 优先的自动选路
- 新安装、保留原规则安装、明确覆盖安装和一条命令升级

## 最简单的安装方式

在 WSL 或 Linux 终端运行：

```bash
curl -fsSL https://raw.githubusercontent.com/digibeing1001/digital-office-agent-system/main/update | bash
```

它会安装到 `~/.hermes`，安装 Skills，并自动跑健康检查和生产门禁。

以后升级只需要：

```bash
~/.hermes/update
```

`update` 只更新程序、配置和内置 Skills，不会把源码目录里的认证缓存、会话、项目、知识库、任务、审批或个人偏好复制到目标环境，也不会在升级时覆盖目标环境里的这些数据。

### 已经有 Hermes 或个人规则

如果目标目录里存在不是 Digital Office 管理的规则或个人数据，安装器会停下来让你明确选择：

```bash
# 保留原来的规则，Digital Office 并排安装
curl -fsSL https://raw.githubusercontent.com/digibeing1001/digital-office-agent-system/main/update | bash -s -- --preserve-existing

# 备份原规则后，让 Digital Office 成为默认秘书入口
curl -fsSL https://raw.githubusercontent.com/digibeing1001/digital-office-agent-system/main/update | bash -s -- --overwrite-existing
```

这是刻意的保护，不会替用户偷偷决定。

### 安装到 OpenClaw

```bash
curl -fsSL https://raw.githubusercontent.com/digibeing1001/digital-office-agent-system/main/update | bash -s -- --host openclaw
```

## 安装后怎么用

安装后，主机的默认入口会成为秘书 Agent（default secretary persona）。正常使用时直接对秘书描述任务即可，例如：

```text
帮我审查这份供应商合同，列出高风险条款和需要业务确认的问题。
```

```text
先调研同类产品，再整理需求，设计界面，最后实现一个可运行的前端版本。
```

```text
把这份材料写成一篇文章，完成事实核对、编辑和终稿检查。
```

管理员可以先做两个快速检查：

```bash
~/.hermes/scripts/agent-router --health
~/.hermes/agent-system/bin/office-system health
```

### 接入本地 Agent、大模型 API 或 Token Plan

打开管理中心的“模型接入”，可以直接选择两类连接：

- **API**：MiniMax、MiMo、Kimi、智谱 GLM、OpenAI、Anthropic、Gemini，或者任意 OpenAI 兼容服务。
- **Token Plan**：MiniMax Coding Plan、MiMo Token Plan、Kimi Code，或者用户自行填写地址的兼容套餐。

每个连接都可以修改 API 地址、模型和密钥，并进行一次真实的小请求测试。密钥保存在服务器本机的私有文件中，权限为 `0600`；浏览器、GUI 状态、审计和运行日志只会看到脱敏尾号。旧有环境变量方式继续兼容。

系统会同时发现本机 Hermes/OpenClaw 和已经配置的 API。你可以选择“本地优先，API 兜底”或“API 优先，本地兜底”，并调整模型顺序。每次选路、模型调用、输入输出 Token 和失败结果都会写入 Loop 预算与运行账本；缺少可用连接时会明确失败，不会伪造成功。

命令行也可以查看连接状态：

```bash
~/.hermes/agent-system/bin/model-gateway status
```

没有配置 API 时会继续使用已发现的本地 Agent，不会因为升级而改变。

如果需要调整工作模式、通知、审批严格度等全局偏好，可以通过管理中心操作，也可以使用受控命令：

```bash
~/.hermes/agent-system/bin/office-system settings-update --work-mode quality --confirmed
```

## 为什么任务交接更稳

系统不会默认把完整聊天历史转发给下一个 Agent。每次交接都会记录：

- 用户真正想完成什么
- 当前目标、限制和验收标准
- 哪些是事实、假设、不确定项或冲突
- 来源和生成产物在哪里
- 已经做过哪些决定
- 哪些内容因篇幅、权限或相关性被省略，以及如何取回
- 接收方是谁、是否验证了交接哈希、是否要求补充上下文

大型文件只保存一次，通过引用传递。私有思维链、密码、密钥和访问令牌禁止进入交接包。

详细说明见 [上下文交接规范](agent-system/docs/context-handoff.zh-CN.md)。

## LOOP 不是无限自我反思

主流 Agent 实践并不存在唯一正确的六步循环。这个项目把运行时收敛为四个能被持久化和测试的节点：

- `Context`：拿到完成下一步所需的可信信息
- `Decide`：形成决定、路线、风险和下一步动作
- `Act`：调用 Agent、Skill 和工具执行
- `Evaluate`：按证据、验收条件、进度和预算判断

模型可以建议下一步，但只有后端控制器能改变状态。简单任务可以跳过 Decide；任务返工可以在批准范围内循环；修改 Agent、Skill、规则、工作流、GUI 契约或发布配置仍然必须由用户确认。

详细说明见 [LOOP 工程](agent-system/docs/loop-engineering.zh-CN.md)。

## 企业数字律师

法务不是律师事务所式的多层 Agent 团队，而是一个企业内设数字律师 `legal`。它可以调用合同审查、公司法、隐私数据、产品合规、用工与知识产权、争议分流和 AI 治理等 Skills。

法律输出是企业内部工作草稿，不替代执业律师意见。正式外发、签署、用工动作、产品上线、诉讼或仲裁必须经过合适的人类专业复核。

本地已安装 Apache-2.0 的 `claude-for-legal-zh`。`Legal-Skills-Chinese` 因 CC BY-NC-ND 4.0 不适合未经授权的商用内置，当前只登记许可证状态，不会激活。

## 图形界面

图形界面分成两个入口：

- `/`：给普通用户使用的“我的办公室”。左侧主导航保留“我的办公室、数字员工、知识库”，底部保留“项目文件夹、设置”。
- `/admin`：给管理员使用的管理中心，包括系统概览、Agent 管理、Skills、运行状态、策略预算、审计和系统维护。

用户端以项目为核心：你可以先把事情告诉秘书，秘书会引导你新建或选择项目；每个项目都有自己的资料、对话、审批、交付物和工作记录。项目里的对话可以像工作线程一样分开，避免所有上下文挤在同一个窗口里。

新项目不会在第一句话之后立刻开跑。秘书会先复述它对用户意图的理解，请用户确认，然后提出至少三道递进问题，引导用户说明真正要改变的结果、谁来判断成功、交付物、不可牺牲的边界、最大失败和原始资料。用户可以在同一对话中上传文件；项目准备度达到门槛并确认底稿后，正式工作才会启动。

“我的办公室”是全局看板，用来快速看到项目、待确认事项、近期交付和整体进度；“项目文件夹”是项目看板，用来管理单个项目的上下文；“知识库”分为公司知识库、项目知识库和个人知识库，并支持从浏览器上传资料；“数字员工”是人事板块，既展示每个 Agent 会做什么，也展示它被调用了多少次、消耗了多少 Token、成功和失败情况，并提示当前系统可能缺少哪些新 Agent。

“我的办公室”和项目页都把秘书对话放在主工作区中央。看板分区可以拖动排序和切换宽度，布局保存在当前浏览器；对话会在新消息和回复出现时自动滚动到当前位置。

管理员可以在界面里创建、停用、恢复、归档和删除自定义 Agent。内置 Agent 受保护，永久删除必须先归档并再次确认，历史任务和审计记录仍会保留。

本机启动：

```bash
~/.hermes/digital-office-gui
```

这条命令会启动本机 GUI，并尽量自动打开浏览器。系统会优先使用 `http://127.0.0.1:8787/`；如果端口已被其他程序占用，会自动寻找下一个可用端口并打开正确地址。常用方式：

```bash
# 打开普通用户界面
~/.hermes/digital-office-gui

# 打开管理后台
~/.hermes/digital-office-gui --admin

# 后台常驻运行
~/.hermes/digital-office-gui --background
```

浏览器可以把它安装为 PWA。监听非本机地址时必须通过 `DIGITAL_OFFICE_WEB_TOKEN` 或 `--token` 配置 Bearer Token；系统不会把项目和任务状态裸露到局域网。需要高级部署时，可以先用 `~/.hermes/agent-system/bin/office-system web-config` 查看配置契约，再用 `~/.hermes/agent-system/bin/office-system web-serve` 接 Caddy、Nginx 或 systemd。

前端直接读取 `gui-state`，所有会改变任务、审批或 Agent 的操作都走专用后端接口。前端不能自己伪造工作流状态，也不能调用任意系统命令。

## 当前完成度

当前是 `0.3.0 internal` 第一版可用界面：

- Agent 与 Skill 责任模型已统一
- 法务已对齐为企业数字律师
- LOOP、上下文交接、权限、审批、恢复和审计契约已落地
- 完整生产 harness 和 smoke 已通过
- Hermes/OpenClaw 安装升级路径已具备
- 用户端和管理后台已经可以正常构建和运行
- Web/PWA 接口具备认证边界，关键写操作有权限、确认和审计
- Agent 生命周期已经纳入生产 harness 和 Web 冒烟测试

也就是说，现在可以用于本机办公、产品演示和内部试用；进入企业稳定发布前，仍需经过试点部署、真实业务数据验证和稳定版发布流程。

## 给开发者和运维人员

常用检查：

```bash
agent-system/bin/harness-check
agent-system/bin/harness-runner --task all --no-write
agent-system/tests/smoke.sh
cd web-ui && npm ci && npm run typecheck && npm run build
```

重要文档：

- [GUI 后端契约](agent-system/docs/gui-contract.md)
- [UI 设计前置就绪说明](agent-system/docs/ui-design-readiness.zh-CN.md)
- [GUI 设计前最终生产审计](agent-system/docs/pre-gui-production-audit.zh-CN.md)
- [生产 harness](agent-system/docs/production-harness.md)
- [企业数字律师](agent-system/docs/digital-lawyer.zh-CN.md)
- [主机规则注入与安装模式](agent-system/docs/host-rule-injection.zh-CN.md)

## 许可证与责任

仓库中的外部 Skill 仍受各自许可证约束。安装登记为“本地可用”不代表可以忽略原作者许可证、数据授权或行业监管要求。

Digital Office 是工作流和 Agent 运行系统，不替代法律、财务、医疗或其他受监管专业人员的最终判断。
