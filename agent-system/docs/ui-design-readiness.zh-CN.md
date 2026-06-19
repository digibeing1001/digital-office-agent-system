# UI 契约与持续就绪说明

本文件最初用于定义 GUI 开工前的后端门禁。第一版用户端和管理后台已经落地后，它继续作为持续契约：GUI 只能消费这些后端状态，不能自己创造另一套业务状态；每次界面或后端变更仍必须通过这里列出的门禁。

## 产品结构

数字办公室采用两层 Agent 责任模型：

1. 用户通过秘书 Agent 下达任务。
2. 秘书把任务交给某项工作的数字员工 Agent。
3. 数字员工 Agent 可以代表部门负责人，但仍然是一个产品可见的责任主体。
4. Agent 下方的“员工”是 Skill，不再建立下级 Agent 组织树。

因此，法务是一个企业内设法务身份的数字律师 Agent `legal`。合同审查、公司法、隐私数据、产品合规、用工与知识产权、争议分流、AI 治理等是它的 Skill 工作通道，不是律师事务所式的多层律师 Agent 团队。

## 后端真相来源

- 数字员工：`agent-system/digital-employees.registry.json`
- Agent 运行注册：`agent-system/agents.registry.json`
- 工作流包与 Skill 通道：`agent-system/workflow-packs.registry.json`
- LOOP 运行时：`agent-system/ai-native-loop.manifest.json`
- 上下文信封：`agent-system/context-envelope.schema.json`
- 上下文交接策略：`agent-system/context-handoff.policy.json`
- Skill 安装与许可证：`agent-system/skill-installations.registry.json`
- 权限、审批和专业判断：`agent-system/identity.access.registry.json`、`judgment.policy.json`
- GUI 后端快照：`office-system gui-state`

## LOOP 与运行状态

正式 LOOP 是 `Context -> Decide -> Act -> Evaluate` 四个工作节点，由后端确定性控制器决定 Continue、Replan、Retry、Wait Human、Complete、Fail、Cancel 或 Budget Exhausted。

GUI 必须直接展示：

- 当前节点和节点状态
- 当前循环次数与进度
- 最大循环、重试、时间、工具和模型预算
- 实际工具、模型、Token 和费用使用量
- 验收结果、失败分类、阻塞原因和等待对象
- 检查点、恢复位置和最后控制决定

简单任务可以由后端明确跳过 Decide。前端不得自己跳节点、自动完成任务或把等待人工处理显示成运行中。

## 上下文交接

交接使用稳定的 `context_id`、`task_id`、`handoff_id` 和 `context_version`。交接包保存短摘要、事实状态、来源、决定、风险、省略声明、权限和上下文预算；大型文档与产物通过引用传递。

GUI 必须区分：

- `pending_acceptance`
- `needs_context`
- `accepted`
- `rejected`

只有接收方身份与 `context_hash` 校验成功后才能调用 `handoff-ack`。未确认的交接不能显示为已完成。

## 人工门禁

高风险专业动作、外部发送、签署、产品上线、用工动作、诉讼仲裁等必须显示人工审批或专业判断状态。私有思维链、密码、密钥和访问令牌不进入 GUI，也不能写入上下文信封。

## 法务 Skill 状态

- `claude-for-legal-zh`：Apache-2.0，已本地安装并由 `digital-lawyer-workflows` 受控调用。
- `Legal-Skills-Chinese`：CC BY-NC-ND 4.0，当前保持许可证阻断；没有商业授权前不得激活、改编或内置到商用工作流。

## GUI 持续交付门禁

每次交付用户端或管理后台前必须通过：

```bash
agent-system/bin/install-skill-sources
agent-system/bin/harness-check
agent-system/bin/harness-runner --task ui-design-readiness-production --no-write
agent-system/bin/harness-runner --task all --no-write
agent-system/tests/smoke.sh
```

还必须完成：

- Python、Shell 和 JSON 静态检查
- React 类型检查和生产构建
- 桌面端与移动端浏览器检查
- 新安装、保留现有数据升级、明确覆盖升级三种安装路径验证
- WSL Hermes 融合验证
- 健康检查、GUI state、Web/PWA 页面和专用写接口验证
- 后端、权限、持久化恢复、上下文交接、发布包的最终审查
- README 按最新产品状态重写并验证一条命令安装/升级入口

任一门禁失败都不能发布，也不能推送 GitHub。
