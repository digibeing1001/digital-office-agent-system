# 待招岗位（按优先级）

## 🥇 P0 — kenny-vibe-designer

**状态**：老板已确认要招，等写完完整 JD 后立即部署
**来源**：从 kenny-vibe-coder 拆出 Design + Creative 域
**预计时间**：本轮会话完成

**前置条件**：
- [x] 老板拍板
- [ ] 写完整 JD
- [ ] 老板二次确认模型配置
- [ ] 部署 + gateway 测试

---

## 🥈 P1 — kenny-pm（产品经理 Agent）✅ 已招

**状态**：2026-06-05 完成本地部署，等 gateway 路由接入 + 真实跑一次验证
**缺口证据**（招前真实数据）：
- 老板有"Router Agent 架构思维"但 PM 主理缺位 → 想法→PRD 全链路没角色
- 本地 `pm-clarity` + 67 个 pm/ skill 没人调 → 大量 PM 弹药闲置
- 产品讨论 / 立项决策只能老板自己想

**核心职责**（实测版本）：
- 5 场景编排：价值发现→逻辑梳理→体验设计→数据/实体→设计交付
- 跨 Agent 翻译（老板话 → planer/coder/designer 能执行的任务）
- 追质询 5-10 轮才出方案，反模式清单自检

**已装资源**（实测版本）：
- 本地 67 个 pm/ skill
- GitHub 136 个 SKILL.md（deanpeters 49 + lenny-skills 86 + ai-pm 1）
- 总计 200+ PM skill
- 路由表：`~/.hermes/profiles/kenny-pm/skills/_pm-system/SKILL-INDEX.md`

**模型建议**（实测版本）：
- 主力：Claude Sonnet 4（深度推理 + 长文连贯）
- 备用：DeepSeek V3.1
- 备注：原 P1 假设"GPT-5.5 跟 designer 同款"是错的实测数据，PM 应走 Claude 系列

**已部署文件**（`~/.hermes/profiles/kenny-pm/`）：
- SOUL.md（10KB / 218 行）— 灵魂文档
- config.yaml（3.7KB）
- skills/_pm-system/SKILL-INDEX.md（4.8KB / 91 行）— 场景→skill 路由表

**协作关系**：
- 调 kenny-researcher 做事实研究（场景 1 后置）
- 调 kenny-planer 做技术方案（场景 4）
- 调 kenny-vibe-designer 出 mockup（场景 3、5）
- 调 kenny-vibe-coder 实现（场景 5 后）
- 调 lark-doc / lark-task 落地（场景 5）

**剩余步骤**：
- [ ] 老板给个真实产品想法跑一次"场景 1 价值发现"
- [ ] 加进 `agent-router` 的 AGENTS 字典
- [ ] 顶层 config.yaml 注册新 agent
- [ ] gateway 重启 + 测试通过

**踩坑记录**（下次招类似 Agent 避免）：
- "灵魂文档"= SOUL.md，**不是** SKILL.md / references/ / jd-template.md（老板纠了 3 轮）
- 正确顺序：装资源 → 写 SOUL.md → 写工作流索引（不要颠倒）
- `clawhub install` 会 hang，用 `env -u HTTPS_PROXY git clone --depth=1` 走直连

---

## 🥉 P2 — 商业顾问 / 财务 Agent

**状态**：远期
**缺口证据**：
- AI Native 咨询业务需要商业模式分析
- AI 相机硬件讨论涉及成本 / 定价 / 众筹 ROI
- KeyStarter 分发涉及合同 / 渠道

**核心职责（推测）**：
- 商业模式画布分析
- 成本拆解 + ROI 测算
- 合同 / 协议初稿

**模型建议**：待定

---

## 历史已招

### kenny-researcher（2026-06-03）
- 模型：Kimi K2.6 + MiMo v2.5 Pro fallback
- 部署路径：`~/.hermes/profiles/kenny-researcher/`
- 是「研究前置硬性规则」的直接产物
