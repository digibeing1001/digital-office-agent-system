# 外部 Skill 库安装模式 + 已知资源地图

> 2026-06-05 招 kenny-pm 时实测。覆盖"装 GitHub skill 库 + 编排进 Agent 工作流"的完整模式。

---

## 一、安装命令（实测可用）

```bash
# 1. 创建导入目录
mkdir -p ~/.hermes/skills/_imported

# 2. 强制直连克隆（绕过 WSL 死代理）
cd ~/.hermes/skills/_imported
env -u HTTPS_PROXY -u HTTP_PROXY -u ALL_PROXY \
  git clone --depth=1 https://github.com/<owner>/<repo>.git

# 3. 验证
find ~/.hermes/skills/_imported/<repo> -name "SKILL.md" | wc -l
```

⚠️ **不要用 `clawhub install`**：是 TUI 模式会 hang，无输出。

⚠️ **WSL 代理 `172.24.112.1:7897` 经常死**：
- 检测：`timeout 5 nc -zv 172.24.112.1 7897` 失败 = 死
- 走直连前先验证网络本身通：`curl -sS -o /dev/null -w "%{http_code}\n" --noproxy "*" https://api.github.com` 应返回 200

---

## 二、GitHub PM 资源地图（2026-06-05 摸底）

### S 级（直接借鉴骨架）
- `deanpeters/Product-Manager-Skills`（4760⭐）— 业内事实标准，49 个 SKILL.md，6 段式格式（Purpose/Key Concepts/Application/Examples/Common Pitfalls/References）
- `RefoundAI/lenny-skills`（1012⭐）— 86 个 skill 源自 Lenny's Podcast，AI 产品 / 用户研究 / 增长 / 团队管理
- `SmileLiuuuu/ai-pm`（6⭐，中文圈）— "5 场景 + Meta 教学"，从模糊想法到产品交付

### A 级（补特定能力）
- `lucasgaravelli/pm-skills-claude-code`（13⭐）— 27 个 PM skill，discovery/delivery/strategy/validation/execution/GTM
- `kazdenc/builder-skills`（39⭐）— PM + 前端 + 全栈 + 浏览器自动化
- `gmaxxxie/ai-native-product-agent-skills`（56⭐）— "AI Native Product Methodology" 80 个 skill P0-P14 阶段
- `assimovt/productskills`（42⭐）— discovery/strategy/prioritization/PRD
- `haabe/mycelium`（30⭐）— 45+ skills + 12 理论 gate（PRD 前质量门）
- `pratikshadake/claude-product-management-skills`（28⭐）— product thinking/discovery/prioritization/launch

### B 级（参考）
- `panda850819/product-management-skill`（27⭐）— Claude Code PM skill（中文）
- `yanivy9h/ai-shipr`（20⭐）— PM OS for Claude Code
- `wwwazzz/senior-pm-prompt`（79⭐）— system prompt 转 Senior PM
- `vishalmdi/ai-native-pm-os`（85⭐）— AI-native PM OS from scratch
- `bdouble/pm-vibecode-ops`（40⭐）— PM + Claude Code/Codex 协作（和 kenny-vibe-coder 互补）

### 搜索关键词
```bash
gh search repos "AI product manager agent" --limit 15 --json name,description,stargazersCount
gh search repos "product management skills claude" --limit 10 --json name,description,stargazersCount
gh search repos "PRD LLM agent" --limit 10 --json name,description,stargazersCount
gh search repos "AI product discovery" --limit 10 --json name,description,stargazersCount
```

---

## 三、SKILL.md 标准格式（deanpeters 6 段式）

```yaml
---
name: <skill-name>           # ≤ 64 字符
description: <一句话>          # ≤ 200 字符
intent: >-                   # 详细意图
type: component | interactive | workflow
theme: <主题>
best_for: [...]
scenarios: [...]
estimated_time: "5-10 min"
---
```

正文结构：**Purpose / Key Concepts / Application / Examples / Common Pitfalls / References**

借鉴而非抄：保留 6 段骨架 + frontmatter 字段，本地写自己版本的正文内容。

---

## 四、工作流编排层（SKILL-INDEX.md 模式）

当 Agent 需要**编排 5+ skill**（不是单点调用）时，建一个独立索引文件：

```
~/.hermes/profiles/<agent-name>/
├── SOUL.md              ← 人设/边界/触发
├── config.yaml
└── skills/
    └── _<system>/
        └── SKILL-INDEX.md   ← 场景→skill 路由表
```

**SOUL.md 与 SKILL-INDEX.md 的分工**：
- SOUL.md：为什么 / 是什么 / 边界（5KB 以内）
- SKILL-INDEX.md：具体调谁（路径表，无废话）

**示例场景分类**（PM Agent 用的）：
1. 价值发现（Value Discovery）
2. 逻辑梳理（Logic Structuring）
3. 体验设计（Interaction Design）
4. 数据/实体（Entity & Data）
5. 设计交付（Design & Handoff）
+ 横切能力（反模式自检 / 用户研究 / 竞品分析 / A/B）

---

## 五、避免的坑

- ❌ 装进来就完事 → ✅ 装完先在 SKILL-INDEX.md 登记路径，否则 PM Agent 找不到
- ❌ 复制原文 → ✅ 借鉴 6 段格式，写自己的内容
- ❌ 一个 SOUL.md 装所有内容 → ✅ 超过 10KB 就拆出 SKILL-INDEX.md
- ❌ 默认走代理 → ✅ WSL 代理经常死，env -u 走直连是稳的

---

## 六、维护节奏

- 每月 1 号做"PM Agent 体检"：跑一次 SKILL-INDEX.md 的 skill 路径是否还能访问（有些 repo 会删/改名）
- 新加 1 个 skill 必须同时：① git pull 仓库 ② 在 SKILL-INDEX.md 登记路径 ③ 验证 SOUL.md 没破
