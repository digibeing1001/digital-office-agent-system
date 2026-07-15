# 飞书前端专家团队

数字办公室支持按任务把需要的专家 Agent Bot 拉入一个飞书群。飞书负责项目空间、@ 交互和可见协作，数字办公室运行时仍负责调度、状态、权限、质量门禁和审计。现有团队里的秘书 Agent 同时就是调度官，不新增第二个控制 Agent。

## 为什么不是 Bot 自由群聊

自由互答会产生回复风暴、重复执行、跨项目串线和权限放大。本实现采用秘书/调度官受控调度：人类只把需求交给秘书；秘书根据任务从候选池提出专家名单；你确认后才允许建群和拉人。专家只消费明确 @ 自己且带 `[DIGITAL_OFFICE_HANDOFF_V1]` 工作包的 Bot 消息。所有事件按 `message_id` 原子去重，并限制 hop 和重复路由边。

## 飞书与 CLI 现状

2026-07-15 实测：`@larksuite/cli` 最新为 1.0.70，本机 1.0.69 已提供所需命令。数字 `5` 只是一次 API 请求的邀请上限，绝不是团队人数预设。系统始终以用户确认的实际名单为准并自动分批：项目需要 7 个 Bot 时，首批建群拉 5 个，再追加 2 个，即 `[5, 2]`；需要 12 个时则是 `[5, 5, 2]`。一个群最终可以有 15 个 Bot。清单中的 Agent 是候选池，不代表全员入群。

每个 Bot 应开通 `im:message.group_at_msg.include_bot:readonly` 并订阅 `im.message.receive_v1`。事件可能重复投递，必须按 `message_id` 去重。

## 建立一个项目群

### 第一次快速导入整个 Agent 候选池

飞书官方 Node SDK 1.61.1+ 提供 `registerApp` OAuth Device Authorization。下面的引导会为清单中的每个 Agent 依次给出 10 分钟有效的在线确认链接；确认后自动创建 Bot 应用、预置消息/群聊/Bot@Bot 权限与长连接事件，把 App Secret 直接通过 stdin 写入对应 lark-cli profile，并只将非秘密 App ID/Open ID 写入 inventory：

```bash
agent-system/bin/feishu-team-bootstrap --manifest agent-system/feishu-team.example.json
# 审阅 dry-run 后执行：
agent-system/bin/feishu-team-bootstrap --manifest agent-system/feishu-team.example.json --confirm-create
```

若要一次导入多个团队，重复传入清单；跨团队 Bot 的稳定身份是 `team_id/agent_id`，因此产品团队与研究团队中同名的 `secretary` 不会被错误合并：

```bash
agent-system/bin/feishu-team-bootstrap \
  --manifest teams/product.json \
  --manifest teams/research.json \
  --manifest teams/writer.json \
  --confirm-create
```

Windows 可先运行 `npm --prefix agent-system/feishu-bootstrap ci --omit=dev --ignore-scripts`，再运行 `node agent-system/bin/feishu-team-bootstrap.mjs ...`。可重复传 `--only researcher` 选中所有团队的同名角色，或传 `--only digital-office-research-team/researcher` 精确选择一个 Bot。中断后用相同 `--output` 重跑会跳过 inventory 中已 ready 的 Bot。

### 让首个飞书 Agent 在对话中逐步引导

先手工建立一个安装引导 Agent，并把它的 lark-cli profile 与接收提醒的群 ID 传给导入器。之后每个缺失角色的授权链接、完成进度、失败重试及最终完成消息都会由该 Agent 发到飞书；用户无需盯着服务器终端：

```bash
agent-system/bin/feishu-team-bootstrap \
  --manifest teams/product.json \
  --manifest teams/research.json \
  --notify-profile office-installer \
  --notify-chat-id oc_xxx \
  --confirm-create
```

这里有三个必须讲清的授权边界：

1. 每个需要成为独立 Bot 身份的角色，首次创建应用时都要分别完成一次在线确认。官方 `registerApp` 的一次调用对应一个应用，不能把多个独立 Bot 合并为一次确认。
2. 角色完成创建并写入 lark-cli profile 后，可反复加入不同项目群；后续建项目不需要重复创建应用或重复这次确认。
3. `lark-cli auth login` 是访问用户个人数据的用户身份授权，与 Bot 应用创建不是一回事。纯 Bot 消息和群组编排不应强迫用户做个人授权；只有日历、云盘等确实需要用户身份的角色才单独请求。

因此支持两种产品模式。`全量预装` 是一次选择多个团队清单，系统逐个引导完成所有缺失角色；`按需导入` 是秘书首次分析任务后，仅对候选编组中 inventory 尚未 ready 的 `team_id/agent_id` 运行导入，再请求用户确认组队。两者共用同一 inventory，角色只导入一次。

App Secret 不会进入 inventory、stdout 或 Git。若同名 lark-cli profile 已存在，导入会 fail closed，不会静默覆盖现有凭据。

### 每个项目按需组队

1. 复制 `feishu-team.example.json`，给项目设置唯一 `team_id`、`project_id`、群名和环境变量。
2. 每个 Bot 使用独立 lark-cli profile。可用 `--inventory .digital-office/feishu-bot-inventory.json` 读取快速导入产生的非秘密标识。
3. 验证清单；秘书/调度官根据任务提出组队方案：

```bash
python3 agent-system/bin/feishu-team-gateway.py --manifest agent-system/feishu-team.example.json --inventory .digital-office/feishu-bot-inventory.json validate
python3 agent-system/bin/feishu-team-gateway.py --manifest agent-system/feishu-team.example.json --inventory .digital-office/feishu-bot-inventory.json staffing-proposal --objective "完成项目调研" --specialist researcher --specialist writer
```

把输出保存为 `staffing.json`。用户确认目标和成员后，显式传回文件内的 `confirmation_token`：

```bash
python3 agent-system/bin/feishu-team-gateway.py --manifest agent-system/feishu-team.example.json --inventory .digital-office/feishu-bot-inventory.json provision-plan --staffing-file staffing.json --confirm-token <confirmed-token>
```

没有匹配的确认令牌，`provision-plan` 会拒绝生成命令。它会同时输出实际的 `selected_bot_count` 和 `batch_sizes`；例如 7 人必须显示 `7` 和 `[5, 2]`。命令本身只输出 argv 数组，绝不建群。人工审阅首条命令并执行，取得 `chat_id` 写入清单指定的环境变量，再执行其余分批拉 Bot 命令。

确认 dry-run 后，可以用同一个 proposal/token 一键执行建群和分批拉人。这个命令要求额外的写确认：

```bash
python3 agent-system/bin/feishu-team-gateway.py --manifest agent-system/feishu-team.example.json --inventory .digital-office/feishu-bot-inventory.json provision-apply --staffing-file staffing.json --confirm-token <confirmed-token> --confirm-write
```

4. 每个 Bot 用自己的 profile 消费事件：

```bash
lark-cli --profile <profile> event consume im.message.receive_v1 --as bot
```

将每行 NDJSON 保存为事件文件后，调用 `route-event`。只有返回 `accepted: true` 才能进入 Agent 工作流。

## 隔离与权限

一个项目一个群、一个 `project_id`、一个状态分区。FDE 团队和研究团队不得共用群 ID 或消息 claim 目录。Bot@Bot 只改变交互入口，不会扩大工具权限；外部发布、付款、权限变更和不可逆操作仍由 `human-gate-actions.policy.json` 控制。

工具不会自动升级 lark-cli。Bot 创建、群创建和成员写入都要求显式确认参数；只有配置 `--notify-profile` 与 `--notify-chat-id` 后，导入器才会用已安装的引导 Agent 发送过程提醒。授权链接不会写入 inventory，App Secret 不会进入聊天。
