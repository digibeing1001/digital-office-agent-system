# GUI 设计前最终生产审计

审计日期：2026-06-19

## 结论

后端、Agent 责任模型、LOOP 运行时、上下文交接、生产 harness、安装更新和 GUI 数据契约已达到正式进入 GUI 设计阶段的条件。本结论表示“可以开始设计并接入 GUI”，不表示视觉 GUI 已完成，也不表示当前 `internal` 版本已经可以跳过试点直接作为公开稳定版销售。

当前没有阻断 GUI 设计的后端缺口。

## 本轮补全的关键能力

- 统一角色模型：秘书负责入口和调度，专业数字员工 Agent 对结果负责，Skill 承担内部工作步骤；系统不再维护多层部门 Agent 树。
- 企业法务统一为一个企业内设数字律师 Agent，通过合同、隐私、合规、公司法、劳动用工、知识产权和 AI 治理等 Skills 工作。
- LOOP 固定为 `Context -> Decide -> Act -> Evaluate` 四个可持久化工作节点，由确定性控制器决定继续、改计划、重试、等待人工、完成、失败、取消或预算耗尽。
- 所有运行具有预算、检查点、恢复、停滞检测、验收条件和哈希链账本；并发写入采用锁保护。
- Agent 交接使用带版本、稳定身份、事实置信度、来源、产物引用、省略说明、权限、哈希和接收确认的结构化上下文包。
- 私有推理链、密码、密钥和访问令牌禁止进入上下文交接包。
- 高风险动作、专业判断和系统自修改保留人工审批或确认边界。
- Web API 在非本机监听时强制 Bearer Token，健康检查保持最小披露，并设置安全响应头。
- 备份覆盖运行、判断、规则提案和日志；恢复会检查归档路径、链接、成员数量和解压大小，使用暂存目录、原子替换和失败回滚。
- 安装和更新区分程序文件与用户运行数据，支持 Hermes、OpenClaw 和通用主机，并要求对已有非托管规则明确选择保留或覆盖。

## 验证证据

- `agent-system/bin/harness-check`：生产任务定义与依赖检查通过。
- `agent-system/bin/harness-runner --task all --no-write`：完整生产门禁通过。
- `agent-system/tests/smoke.sh`：干净安装、路由、健康、Web/PWA 和核心工作流回归通过。
- 真实 WSL Hermes 已完成安装更新；更新前后 91 个现有认证、缓存、会话和运行数据文件哈希一致。
- 真实 Hermes 的路由健康、办公室健康、`gui-state` 和 harness 检查通过。
- GitHub Actions 会在主分支推送和 Pull Request 上重新执行生产门禁与干净安装 smoke。

## 允许 GUI 依赖的稳定契约

- `office-system gui-state`：数字员工、工作流、Skills、LOOP、预算、上下文交接和运行状态的只读聚合视图。
- `office-system settings-update`：受控设置写入入口。
- `agent-system/docs/gui-contract.md`：前端字段、状态和安全边界。
- `agent-system/context-envelope.schema.json` 与 `agent-system/context-handoff.policy.json`：上下文包和接收确认规范。
- `agent-system/ai-native-loop.manifest.json`：LOOP 节点、控制决策、预算和终止语义。

前端只能展示和请求后端动作，不能自行伪造任务状态、审批结果、Agent 交接确认或 LOOP 控制决策。

## 非阻断项与发布边界

- 最终视觉、交互和信息架构仍待 GUI 阶段完成。
- 当前发布通道是 `internal`。转为公开 `stable` 前仍需完成候选版本签名或校验和、试点部署、真实模型与外部服务环境验证以及回滚演练。
- OCR、PDF 解析和外部检索依赖按工作流需要安装；未安装时健康检查会将其标为可选能力，不能静默宣称已经处理相关文件。
- `claude-for-legal-zh` 已按许可证本地内置；`Legal-Skills-Chinese` 因非商业、禁止演绎条款未获额外授权，保持登记但不激活。

## 放行决定

**放行进入 GUI 设计。** GUI 团队应以现有后端契约为唯一状态来源；任何需要修改契约的设计变更，都必须同时增加迁移策略和 harness 回归门禁。
