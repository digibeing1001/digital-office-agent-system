# 数字办公室宿主规则注入策略

## 目标

数字办公室套件面向可分发部署，而不是绑定某一个本地 Agent 工具。套件可以安装到 Hermes、OpenClaw 或其他兼容宿主中。安装完成后，宿主的默认 Agent 承担数字办公室秘书 Agent 职责，并优先加载本套件的 `agent-system/` 注册表、规则、工作流、门禁和发布策略。

## 默认 Agent 注入

- Hermes 宿主：安装器将 `SOUL.md` 注入为默认 Agent 入口。
- OpenClaw 宿主：安装器将同一套秘书入口注入为 `AGENTS.md`。
- 其他兼容宿主：安装器使用 `AGENTS.md` 作为默认入口文件。

默认 Agent 被注入后必须执行秘书职责：收口需求、选择角色和工作流、管理交接、执行门禁、保护知识和权限边界，并给出最终交付说明。不得再沿用宿主原始默认 Agent 的本地规则作为最高优先级。

## Clean Host 行为

如果目标宿主是干净的新安装环境，安装器默认执行规则注入：

```bash
./install.sh --host hermes --target ~/.hermes
./install.sh --host openclaw --target ~/.openclaw
```

clean install 会把数字办公室入口写入宿主默认规则文件，并同步 `agent-system/`、`scripts/`、`profiles/`、`skills/` 和 README。安装后会运行路由健康检查、系统健康检查、harness 检查和产品更新状态检查。

## Non-Clean Host 行为

如果目标宿主已有个人规则、用户偏好、项目、知识库、任务记录或运行记录，安装器不能静默覆盖。管理员必须选择：

- `--preserve-existing`：保留宿主原入口和个人数据，数字办公室安装到 `digital-office/` 子目录，供管理员审查后再切换。
- `--overwrite-existing`：备份原入口文件，再把数字办公室秘书入口写入宿主默认入口。

示例：

```bash
./install.sh --host openclaw --target ~/.openclaw --preserve-existing
./install.sh --host openclaw --target ~/.openclaw --overwrite-existing
```

## 产品发布要求

每次产品更新都应以可分发版本为目标进行 review：

1. 用户主机上可以完成安装、注入、健康检查和回归检查。
2. 关键工作流可以闭环，不能只停留在文档或手动步骤。
3. 默认 Agent 的秘书职责、角色边界、知识权限和交付门禁保持一致。
4. 中文 README 面向用户和开发者，说明产品能力、安装方式、验证方法和开发更新，不写成本地个人使用记录。
5. 更新需要同步到 WSL Hermes 开发目录，并上传到 GitHub。

## 当前更新日志

### 2026-06-09

- 新增 Hermes、OpenClaw 和 generic 宿主注入策略。
- clean install 默认注入数字办公室秘书入口。
- non-clean install 必须选择保留并行安装或显式覆盖。
- 默认 Agent 被定义为秘书 Agent，接管需求收口、路由、交接、门禁和交付说明。
- PPT 工作流调整为 `intake -> writing -> design -> intake`：Writer 负责故事线、文案和讲稿；Designer 负责视觉方向和可渲染 deck artifact；秘书负责收需求、门禁和交付。
