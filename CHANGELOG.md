# 开发进度日志

本文件记录数字办公室 Agent System 的开发进度。每次产品更新同步到此文件。

---

## 2026-06-18

### 新增

- **企业法务部门架构**
  - 新增 `agent-system/departments.registry.json`，把“部门”定义为能力命名空间、权限边界、知识空间和工作流包，而不是僵硬复刻人类组织层级。
  - 新增企业法务部 Agent：`legal`、`legal-contracts`、`legal-compliance`，覆盖法务收口、合同审查、合规与产品法务、综合法务结论整理。
  - 新增法务工作流：`legal_triage`、`legal_contract_review`、`legal_product_compliance_review`、`legal_privacy_data_review`、`legal_employment_ip_review`、`legal_dispute_triage`。
  - 新增内部技能 `skills/legal-department-workflows/SKILL.md`，要求法务输出保持为企业内部审查草稿，重大法律判断、外部函件、签署、上线或监管动作必须经过人工专业复核。
  - 新增 `agent-system/docs/legal-department.zh-CN.md` 和 `agent-system/harness/tasks/legal-department-production.json`，记录法务部门设计、路由、来源库边界和生产验证门禁。

### 变更

- 架构文档新增 Department layer：秘书 Agent 可以把任务派发到部门工作流，但运行时仍按最小必要拓扑选择直接专家、部门流程或负责人综合，不强制模拟多级管理链。
- `secretary.capabilities.json` 新增法务工作流治理规则：需要引用来源文件或标记法律依据未验证，并在高风险法律场景触发人工复核。
- 外部法务技能来源登记：
  - `claude-for-legal-zh`：Apache 2.0，作为可分阶段引入的企业法务技能参考源。
  - `Legal-Skills-Chinese`：CC BY-NC-ND 4.0，登记为仅参考和许可审查候选，不在未获授权前商用、改编、内置或再分发。

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
