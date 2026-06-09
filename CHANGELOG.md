# 开发进度日志

本文件记录数字办公室 Agent System 的开发进度。每次产品更新同步到此文件。

---

## 2026-06-10

### 新增

- **Coder Agent 能力迭代 — 集成 vibe-coding-production-harness**
  - 来源：https://github.com/digibeing1001/claude-vibe-coding-setup
  - 新增 skill：`skills/vibe-coding-production-harness/SKILL.md`（含 Soul Principles + 8 阶段 + 六角色 + 质量门）
  - `profiles/office-coder/SOUL.md`：新增 Primary Skill / Quality Bar / Cross-Session Memory Discipline 三段
  - `agent-system/agents.registry.json`：coder 节点绑定 `primary_skill` / `default_skill_chain` / `quality_gates` / `source_iteration`
  - 跨 profile 同步：与 `~/.hermes/profiles/kenny-vibe-coder/SOUL.md` 共享方法论，差异仅 voice + overlay
  - KeyMemory entity：`545d2fb5-43e3-4367-a2bb-fa12addd1f99`（规则4：harness 主入口）
  - 公共根 ↔ 仓库端 byte 一致（sha256 `60aeff3456e86076...`）

### 设计决策

- 不搬运 Claude Code 的 120+ Toolkit Plugin，改为映射到 Hermes 原生 skill（a11y/bundle/dead-code 等由 harness Quality Gate 内置）
- 跨会话记忆走 KeyMemory（全局硬规则2），不引入 Claude Mem
- SOUL.md 说 "why + boundaries"，harness SKILL.md 说 "how"，不重复路由逻辑

## 2026-06-09

### 新增

- **PPT 生产工作流** (`ppt_production`)
  - 流程：`intake → writing → design → intake`
  - 秘书负责需求收口和最终交付
  - Writer 负责故事线、页面文案、标题层级、讲稿和事实表述
  - Designer 负责视觉方向、版式、媒体决策和可渲染 deck artifact
  - 新增 harness 任务：`ppt-production.json`

- **宿主注入策略**
  - 支持 Hermes、OpenClaw 和 generic 宿主
  - 干净宿主自动注入数字办公室规则
  - 已有个人规则的宿主必须选择并行保留或显式覆盖
  - 新增 `host-injection.policy.json`
  - 新增 harness 任务：`host-injection-production.json`

- **PPT 外部技能来源登记**
  - `humanize-ppt` — 文案去 AI 痕迹
  - `huashu-design` — HTML 原型与设计变体
  - `guizang-ppt-skill` — 横向翻页网页 PPT
  - `frontend-slides` — 动画丰富 HTML 演示
  - `pitch-clarity-coach` — 仅研究用，不作为生产秘书技能启用

- **安装器增强**
  - 新增 `--host`、`--overwrite-existing`、`--preserve-existing`、`--no-check` 选项
  - 安装后自动运行健康检查

### 变更

- 默认宿主 Agent 明确注入为数字办公室秘书 Agent
- 秘书人设改为中性基线，不绑定个人名称或偏好
- 内置 Agent Profile 去个人化：Digital Office Coder、Planner、Product Manager、Researcher、Designer、Writer
- 主 README 重写为面向用户和开发者的产品说明
- 开发进度日志独立到 CHANGELOG.md

### 文档

- 新增 `agent-system/docs/host-rule-injection.zh-CN.md`
- 新增 `agent-system/docs/ppt-production-workflow.md`
- 更新 `agent-system/docs/architecture.md`

---

## 2026-06-05

### 新增

- **三条全局硬规则**
  1. 新建 Agent 必须先注册 agent-router
  2. 先验证再写（验证结果存 KeyMemory entity）
  3. 全局规则默认同步所有 Agent（4 位置：KeyMemory + SOUL.md + profile SOUL.md + profile config.yaml）

---

## 早期开发

- Agent 注册表 (`agents.registry.json`) 基础结构
- 智能路由器 (`scripts/agent-router`) 实现
- 秘书能力配置 (`secretary.capabilities.json`)
- 质量门禁框架 (`harness-check` / `harness-runner`)
- AI Native 闭环定义
- Web UI / PWA shell 后端
- 知识库与记忆分层架构
- GUI 后端控制面 (`office-system.py`)
