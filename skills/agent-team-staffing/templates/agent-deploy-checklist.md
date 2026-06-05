# 领域型 Agent 部署清单模板（kenny-pm 实测范式）

> 用于复制后修改，部署新的"领域型"Agent 时直接套用。

## 路径与文件

```
~/.hermes/profiles/kenny-<name>/
├── SOUL.md                          # 灵魂文档（必须）
├── config.yaml                      # profile 配置（必须）
└── skills/
    └── _<system>/                   # 内部系统 skill（可选）
        └── SKILL-INDEX.md           # 场景→skill 路由表（多 skill 时必加）
```

## 灵魂文档 SOUL.md 必含段落（按顺序）

1. **# <Name>** — 标题 + 一句话角色定位
2. **Role + Voice** — 1-2 句角色 + 1-2 句语气（冷静/热情/软萌……）
3. **触发条件** — 触发词清单（明确说"什么是我的活"和"什么不是我的活"）
4. **核心信念** — 3-5 条不可妥协的做事原则
5. **<N> 场景骨架** — 把用户场景拆成 3-7 个具体场景，每个说"用户说什么 → 我干什么 → 产出什么"
6. **工具箱** — 表格：调谁 / 路径 / 用途
7. **工作流协议** — 入口识别 → 路由 → 追问 → 调 skill → 自检 → 交付
8. **跨 Agent 切换必须通知**（用户硬性规则）
9. **反模式清单** — 5-10 条常见错，每条格式「症状 / 为什么错 / 正确做法」
10. **模型** — 主力 + 备用 fallback + **明确写"待用户确认"**（不要自主拍板）
11. **自检清单** — checkbox 形式，每次完成工作时过一遍
12. **启动方式** — 1-2 句怎么调

## config.yaml 必含字段（最小集）

```yaml
model:
  context_length: 409600
  default: <model-name>            # 不要自主拍板，写"待用户确认"
  provider: <openrouter | openai-codex | anthropic | ...>
fallback_model:
  - provider: <...>
    model: <fallback-model>
toolsets:
- hermes-cli
- feishu_doc                      # 写文档/拉取
- feishu_drive                    # 存文件
agent:
  max_turns: 90
  reasoning_effort: high          # 深度推理任务设 high
```

## 部署子步（2026-06-05 实测标准）

```
0a. 决定装哪些外部 skill（基于 PM 类 / coding 类等已知 skill 库）
0b. ⚠️ 不要用 `clawhub install`（TUI 模式 hang）
0c. 改用 git clone --depth=1，强制直连绕过坏代理：
    env -u HTTPS_PROXY -u HTTP_PROXY -u ALL_PROXY \
      git clone --depth=1 <repo-url> ~/.hermes/skills/_imported/<name>
0d. 验证：find ~/.hermes/skills/_imported/<name> -name "SKILL.md" | wc -l

1. mkdir -p ~/.hermes/profiles/kenny-<name>/skills
2. 写 config.yaml（参照本模板）
3. 写 SOUL.md（灵魂文档，详上方 12 段必含）
4. 写 skills/_<system>/SKILL-INDEX.md（场景→skill 路由表）
5. 调 agent-router 加路由
6. ⚠️ 停下来让用户手动改顶层 ~/.hermes/config.yaml
7. ⚠️ 让用户重启 gateway
8. 跑 /home/zexin/.hermes/scripts/agent-router --agent kenny-<name> "test" 验证
```

## 模型选型（2026-06-05 用户拍板硬数据）

| 场景 | 推荐 | 原因 |
|---|---|---|
| 5-10 轮追问对话 | GPT-5.5 | 拟人感最强 |
| 结构化长文输出 | Claude Sonnet 4 | 最稳、不超时、output token 最低 |
| 中文场景 + 性价比 | Xiaomi MiMo V2.5 Pro | 中文强、成本低 |
| 长尾深度推理 | Claude Sonnet 4 | DeepSeek V4 Pro 在长任务上超时严重（实测 240s × 5 重试） |
| 绝对不能选 | DeepSeek V4 Pro | OpenRouter 上 reliability 不行，3/13 prompt 直接挂 |

数据来源：
- 独立 benchmark：[dakshjain-1616/Claude-Opus-4.7-vs-GPT-5.5-vs-DeepSeek-V4-Pro-Reasoning-Benchmark](https://github.com/dakshjain-1616/Claude-Opus-4.7-vs-GPT-5.5-vs-DeepSeek-V4-Pro-Reasoning-Benchmark) — 13 hard prompt，独立 judge，2026-04-27
- 实战项目：[7as0nch/mimo2codex](https://github.com/7as0nch/mimo2codex) — Codex CLI 接 MiMo/DeepSeek 的第一手工程经验

## SOUL.md 必加的 4 条用户硬性规则

1. **追问 5-10 轮才能出方案**（少于 5 轮 = 任务失败）
2. **每次只问 1 个最关键问题**（不要一次甩 5 个）
3. **价值锚点不清不进入下一阶段**
4. **跨场景必须留 context**（上一场景产出作为下一场景输入）
5. **反模式自检是必经环节**（产出自检 + 用户自检）
6. **🔄 切换至 [Agent名] / 模型：[模型名]**（跨 Agent 调用时必发通知）

## 反模式（灵魂文档的"必检清单"）

任何领域型 Agent 的 SOUL.md 都该有"反模式清单"，模板：

```
### ❌ 反模式 1：<症状>
- **症状**：<具体表现>
- **为什么错**：<根因>
- **正确做法**：<正确路径>
```

5-10 条反模式比 50 条"工作流要点"管用——**反模式是护栏，工作流是路径**。

## 验证清单（部署完跑）

- [ ] SOUL.md 12 段都齐？
- [ ] config.yaml 必含字段都齐？
- [ ] 调 `hermes --profile kenny-<name>` 启动正常？
- [ ] 跑一个真实任务看 Agent 触发/不触发是否正确？
- [ ] 跨 Agent 切换时通知消息发了吗？
- [ ] 反模式清单过一遍能过？

## 反例（2026-06-05 老板纠正 3 轮才听懂）

老板说"灵魂文档"时**默认指 SOUL.md**：
- ❶ 老板说"写灵魂文档" → 我去写一个新 SKILL.md → 老板纠正是 SOUL.md
- ❷ 老板说"写到灵文文档"（口误，"灵文" = "灵魂"）→ 我猜飞书 doc → 老板纠正是 SOUL.md
- ❸ 老板说"先安装 skill 再写灵魂文档" → 我先写 SOUL.md → 老板纠正要**先装再写**

**正确顺序**：确认需求 → 安装/盘点资源 → 写 SOUL.md → 写工作流索引 → 用户确认 → 部署。**不要颠倒**。
