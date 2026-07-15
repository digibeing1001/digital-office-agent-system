# 飞书前端专家团队

数字办公室支持按任务把需要的专家 Agent Bot 拉入一个飞书群。飞书负责项目空间、@ 交互和可见协作，数字办公室运行时仍负责调度、状态、权限、质量门禁和审计。现有团队里的秘书 Agent 同时就是调度官，不新增第二个控制 Agent。

## 为什么不是 Bot 自由群聊

自由互答会产生回复风暴、重复执行、跨项目串线和权限放大。本实现采用秘书/调度官受控调度：人类只把需求交给秘书；秘书根据任务从候选池提出专家名单；你确认后才允许建群和拉人。专家只消费明确 @ 自己且带 `[DIGITAL_OFFICE_HANDOFF_V1]` 工作包的 Bot 消息。所有事件按 `message_id` 原子去重，并限制 hop 和重复路由边。

## 飞书与 CLI 现状

2026-07-15 实测：`@larksuite/cli` 最新为 1.0.70，本机 1.0.69 已提供所需命令。创建群时一次最多邀请 5 个 Bot，后续每次也最多邀请 5 个，但一个群最终可以有 15 个 Bot。清单中的 Agent 是候选池，不代表全员入群。

每个 Bot 应开通 `im:message.group_at_msg.include_bot:readonly` 并订阅 `im.message.receive_v1`。事件可能重复投递，必须按 `message_id` 去重。

## 建立一个项目群

### 第一次快速导入整个 Agent 候选池

飞书官方 Node SDK 1.61.1+ 提供 `registerApp` OAuth Device Authorization。下面的引导会为清单中的每个 Agent 依次给出 10 分钟有效的在线确认链接；确认后自动创建 Bot 应用、预置消息/群聊/Bot@Bot 权限与长连接事件，把 App Secret 直接通过 stdin 写入对应 lark-cli profile，并只将非秘密 App ID/Open ID 写入 inventory：

```bash
agent-system/bin/feishu-team-bootstrap --manifest agent-system/feishu-team.example.json
# 审阅 dry-run 后执行：
agent-system/bin/feishu-team-bootstrap --manifest agent-system/feishu-team.example.json --confirm-create
```

Windows 可先运行 `npm --prefix agent-system/feishu-bootstrap ci --omit=dev --ignore-scripts`，再运行 `node agent-system/bin/feishu-team-bootstrap.mjs ...`。可重复传 `--only researcher` 只创建指定 Bot。中断后用相同 `--output` 重跑会跳过 inventory 中已 ready 的 Agent。

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

没有匹配的确认令牌，`provision-plan` 会拒绝生成命令。它本身也只输出 argv 数组，绝不建群。人工审阅首条命令并执行，取得 `chat_id` 写入清单指定的环境变量，再执行其余分批拉 Bot 命令。

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

当前工具不会自动升级 lark-cli、创建群、拉 Bot 或发送消息；这些都是需要人工审阅配置后执行的外部写操作。
