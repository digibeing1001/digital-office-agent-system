# Digital Office Writer Team 中文说明

Writer Team 是 Digital Office 的写作团队特化分支，面向公众号、知乎、小红书、博客、产品文章、发布说明和长文 insight 等内容生产场景。它保留 Hermes/OpenClaw 可部署底座，同时把默认角色收敛为秘书、选题官、研究员、大纲师、撰稿人、审查员、风格官和排版师。

## 核心设计目标

- 一个秘书入口接活，先确认读者、价值承诺、边界和发布平台，再启动写作流水线。
- 每个角色只负责一段工作，避免一个 Agent 同时选题、查证、写稿、审稿和排版。
- 关键 Gate 必须停下来等确认，防止 AI 跳过素材、结构、初稿、审查、去 AI 味和终稿审批。
- 事实、引用、风格画像、审查意见和返工原因都要写入工作包，便于复盘和长期学习。
- 输出默认是企业内部草稿；公开发布、外发、署名、合规和品牌风险动作必须由人确认。
- 同一写作 run 使用 durable dispatch lease 防止重复派发；一个角色能完成时默认 Solo，只有事实核验、独立并行或作者/编辑隔离有明确价值时才组队。

## 部署与运行

推荐在 WSL 或 Linux 环境安装到 Hermes/OpenClaw 主目录：

```bash
git clone -b writer-team https://github.com/digibeing1001/digital-office-agent-system.git
cd digital-office-agent-system
./install.sh --host hermes --target ~/.hermes
```

已有 Hermes/OpenClaw 本地规则、个人资料或企业数据时，安装器必须使用保留并行安装或明确覆盖选项，避免误覆盖现有 `SOUL.md`、`AGENTS.md` 和运行数据。

图形界面：

```bash
web-config
web-serve
```

普通入口是 `/`，管理后台入口是 `/admin`。PWA 会注册 `manifest.webmanifest` 和 `service-worker.js`，适合内容团队在内网或单机环境使用。

## 开发更新记录

- 2026-07-11：同步 durable dispatch lease、双进程并发回归、崩溃过期恢复、checkout 隔离健康检查和逐 gate harness 进度。
- 2026-07-11：CI 覆盖 writer-team，并在本分支没有源码 `web-ui/` 时跳过 Node source build、继续验证已打包 Web/PWA；新增 Solo-first 论文依据与协调验证。
- 2026-07-08：补齐 writer-team 的中文发行说明和 Hermes/OpenClaw 安装说明。
- 2026-07-08：恢复生产 harness skills、legal source pack 和 Web/PWA 运行门禁所需的运行文件。
