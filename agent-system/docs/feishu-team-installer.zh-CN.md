# 飞书 Agent 团队安装器

团队安装器用于把已经安装在 Digital Office/Hermes/OpenClaw 宿主中的 Agent 团队接入飞书。它负责创建或复用飞书 Bot 身份、生成独立 CLI profile，并把首次 OAuth 授权过程变成可跟踪的安装会话；它不替代底层 Agent 宿主和团队能力包的安装。

## 使用前准备

统一部署器应先安装：

- Digital Office 与 Hermes/OpenClaw Agent 宿主；
- Node.js 20+ 与 npm；
- 统一部署器按 lockfile 本地安装的官方飞书 CLI 与飞书 SDK；
- 计划导入团队对应的运行时能力包。

进入 `/admin` 后打开“团队安装器”。预检卡片会明确显示缺失组件；预检未通过时，创建按钮保持禁用。

## 一键导入流程

1. 从团队目录多选需要的团队，并展开卡片核对角色。
2. 查看角色总数、已经就绪的角色和预计首次确认次数。
3. 如需飞书内提醒，填写引导 Agent 的 CLI profile 与目标群 `chat_id`。
4. 勾选明确确认，点击“一键导入所选团队”。
5. 对每个缺失角色打开页面提供的授权链接，依次完成在线确认。
6. 页面显示全部角色就绪后结束；后续项目复用这些角色，不重复授权。

一次提交可以包含任意数量的目录角色。执行器逐个处理首次授权，因此某个飞书操作的单次批量上限不会被当作团队人数上限。

## 可靠性与安全边界

- `team_id`、`agent_id` 和 profile 名称稳定，重复运行会读取 inventory 并复用已完成角色。
- 不接受浏览器提交任意 manifest 路径；可选团队必须来自服务器端受控目录。
- 安装 API 仅允许管理员访问，开始创建前必须传入 `confirmed: true`。
- OAuth 密钥与 token 不写入浏览器响应、NDJSON 事件或审计日志。
- 会话事件保存在私有运行目录，可恢复查看当前授权角色、成功数、失败数和错误摘要。
- 一个角色失败时会记录失败事件和进程退出状态；修复环境后重新提交相同团队即可复用已成功角色并继续缺失角色。

## CLI 诊断

在仓库根目录运行：

```bash
python3 agent-system/bin/feishu-team-installer.py catalog
python3 agent-system/bin/feishu-team-installer.py plan --team product --team research
```

`catalog` 返回团队目录和环境预检；`plan` 只计算计划，不创建飞书应用。真实创建应优先从管理后台发起，以保留明确确认、会话进度和审计记录。

## Web API

- `GET /api/installer/catalog`：返回受控团队目录、角色复用状态与环境预检。
- `POST /api/installer/sessions`：提交 `teams`、`confirmed` 及可选提醒配置，启动后台安装会话。
- `GET /api/installer/sessions/{session_id}`：读取当前授权链接、进度、事件和最终状态。

生产环境在非本机监听时仍遵循 Digital Office 的 Bearer Token 与管理员角色控制。
