# 外部工具方法论参考库

> 本文件汇总 GitHub 调研的 10 个项目核心方法论，按 Agent 角色分组，供各角色卡引用。
> 已下载项目：humanize-chinese-writing（见 `tools/downloaded/humanize-chinese-writing/`）
> 其他项目以方法论提炼形式接入，不下载源码。

---

## 一、审查员承载（去 AI 味核心方法论）

### 1.1 humanize-chinese-writing（已下载本地）

**本地路径**：[tools/downloaded/humanize-chinese-writing/](../downloaded/humanize-chinese-writing/)
**关键文件**：
- `README.md` ——「回答者惯性」理论与五层检查方法论
- `references/patterns.md` —— 中文 AI 味 6 大类模式（结构/信息/句式/节奏/文体/复读）
- `scripts/audit_chinese_ai_style.py` —— 机械审计脚本，识别 9 类风险

**核心理论**：回答者惯性——AI 把聊天里的确认、纠正、补充、总结、邀约姿态带进成品，文本完整礼貌却像被拉长的聊天回复。

**落笔前四步**：
1. 确定文本任务（文体/读者/场景/需知需信需做/事实边界）
2. 建立作者站位（脱离聊天上下文独立成立）
3. 选择组织原则（说明/教程/分析/介绍/叙事各有主线）
4. 写出并检查首稿（从具体对象起笔，不追加服务式收尾）

**交付前五层检查**：
1. 站位层——正文能否脱离聊天上下文独立成立
2. 结构层——段落由主题推动，还是提示词逐项扩写
3. 信息层——空泛背景/同义复述/价值膨胀/模糊归因
4. 句式层——纠正式模板/元话语/虚化动词过密
5. 节奏层——句长/段长/句首/连接词/标点是否整齐失变化

**9 类审计风险**（脚本可识别）：模板对立、回答者姿态、空泛开场、宣传腔、机械连接、连续短句、重复句首、段落等长、AI 工具残留标记

**方法边界**：不承诺绕过 AIGC 检测、不用错别字病句制造人味、不删证据条件限定词、不改写需逐字保留的来源文本

---

### 1.2 blader/humanizer（33 模式检查表，英文参考）

**仓库**：https://github.com/blader/humanizer （33k+ Star）
**性质**：基于 Wikipedia "Signs of AI writing" 的可移植 skill，含两轮改写+审计 pass
**重要**：实际为 **33 个模式**（非 24 个），按 5 类组织：

**A. 内容模式（6 个）**
1. 意义膨胀（Significance inflation）
2. 名人背书（Notability name-dropping）
3. 肤浅 -ing 分析
4. 推销语（Promotional language）
5. 模糊归因（Vague attributions）
6. 公式化挑战（Formulaic challenges）

**B. 语言模式（7 个）**
7. AI 词汇（actually/additionally/testament/landscape/showcasing）
8. 系词回避（serves as/features/boasts）
9. 否定并列/尾随否定（"It's not just X, it's Y"）
10. 三段式（Rule of three）
11. 同义词循环（Synonym cycling）
12. 虚假范围（False ranges）
13. 被动语态/无主语片段

**C. 风格模式（10 个）**
14. 破折号滥用
15. 粗体滥用
16. 内嵌标题列表（Inline-header lists）
17. Title Case 标题
18. emoji
19. 弯引号
20. 聊天机器人痕迹（"I hope this helps"）
21. 截断免责（"While details are limited..."）
22. 谄媚语气（"Great question!"）
23. 填充短语（"In order to"）
24. 过度对冲（"could potentially possibly"）
25. 通用结论（"The future looks bright"）
26. 连字符词对
27. 权威套路（Persuasive authority tropes）
28. 路标宣告（"Let's dive in"）
29. 碎片标题
30. 差异锚定写作
31. 制造金句/断奏戏剧
32. 格言公式
33. 会话式开场（"Honestly? It depends..."）

**改写流程**：识别 → 改写 → "obviously AI generated" 审计 → 二次改写

**中文适配建议**：英文模式不能直接套用，需映射为中文等价物。例如：
- "It's not just X, it's Y" → 中文「不是 X，而是 Y」纠正式句型（已在 humanize-chinese-writing 模式 3.1 列出）
- "In order to" → 中文「为了」「旨在」（虚化动词模式 3.5）
- "Let's dive in" → 中文「下面让我们深入探讨」（元话语模式 3.2）

---

### 1.3 humanify（仓库不可访问，方向性参考）

**仓库**：https://github.com/PiaoXiaoTian/humanify（抓取失败，疑似不存在或私有）
**方向性策略**：
- 句式多样化：长短句混合、倒装、设问、断句，制造呼吸感
- 个人化语气注入：第一人称视角、口语化语气词、个人判断与情绪词
- 避免模板化：识别并改写套路化开头/结尾/过渡句

**建议**：以 humanize-chinese-writing 的 patterns.md 为主检查表，humanify 的策略作为补充思路融入审查员 Step 7。

---

## 二、排版师承载（多平台排版方法论）

### 2.1 doocs/md（在线版可用，无需下载源码）

**在线版**：https://md.doocs.tech
**仓库**：https://github.com/doocs/md （9k+ Star）

**核心方法论**：
- **主题 = CSS 样式表**：内容与样式彻底分离，切换主题即换 CSS
- **图床统一抽象**：支持 GitHub/阿里云/腾讯云/七牛云/MinIO/S3/公众号/Cloudflare R2/又拍云/Telegram/Cloudinary 等 10+ 图床
- **语法扩展**：标准 Markdown + KaTeX 数学公式 + Mermaid 图表 + PlantUML + GFM 警告块 + Ruby 注音

**对排版师的启示**：
- 维护「主题 CSS 库」，每个平台一份
- 图片统一走图床接口，撰稿人只需贴 URL
- 代码块独立高亮主题

---

### 2.2 mdnice（在线版可用，无需下载源码）

**在线版**：https://mdnice.com
**仓库**：https://github.com/mdnice/markdown-nice （4k+ Star）

**核心方法论**：
- **一份 Markdown + 多套主题 CSS → 多平台适配**
- **主题库可社区复用**：主题作为可独立提交、分享的资产
- **平台特有规则兜底**：各平台 CSS 支持度不同（知乎部分样式不支持、公众号代码块规则特殊）

**对排版师的启示**：
- 维护公众号/知乎/掘金/小红书四份主题 CSS
- 每平台一份适配规则清单（支持标签、禁用 CSS、代码块规则、外链规则）
- 出稿时按目标平台自动套用对应主题 + 规则校验

---

## 三、选题官承载（热点雷达数据源）

### 3.1 DailyHot / DailyHotApi（API 形式接入，无需下载源码）

**正确仓库**：
- 前端：https://github.com/imsyy/DailyHot
- API：https://github.com/imsyy/DailyHotApi

**支持 40+ 平台**（按类别）：

| 类别 | 平台 |
|---|---|
| 视频/社区 | 哔哩哔哩、AcFun、微博、贴吧、豆瓣电影/小组、快手、抖音 |
| 资讯/科技 | 知乎、知乎日报、百度、今日头条、36氪、51CTO、CSDN、IT之家、少数派、简书、果壳、澎湃、腾讯新闻、新浪、新浪新闻、网易新闻、虎嗅、爱范儿、稀土掘金、NodeSeek |
| 论坛/极客 | 吾爱破解、全球主机交流、酷安、虎扑、NGA、V2EX、HelloGitHub |
| 游戏/读书/天气 | 英雄联盟、米游社、原神、崩坏3、星穹铁道、微信读书、中央气象台 |

**调用方式**：统一路由 `/{调用名称}`（如 `/weibo`、`/zhihu`、`/36kr`），支持 RSS + JSON 双模式

**对选题官的启示**：
- 用统一热榜 API 轮询 40+ 平台，按类别（热搜榜/热榜/推荐/快讯）筛选去重
- 平台分类映射选题维度：热搜榜→大众话题；热榜→垂直行业；推荐→长尾选题
- 支持两种接入：RSS 订阅（被动监听）+ JSON 调用（主动查询）

---

### 3.2 newsnow（支持 MCP server，可被 Agent 直接调用）

**仓库**：https://github.com/ourongxing/newsnow （3k+ Star）

**核心方法论**：
- **数据源双层架构**：`shared/sources`（类型定义）+ `server/sources`（抓取实现）分离，新增源只改实现层
- **自适应抓取频率**：按源更新频率动态调整间隔（最小 2 分钟），30 分钟默认缓存
- **MCP server 接入**：Agent 可通过 MCP 协议直接读取热点数据

**对选题官的启示**：
- 数据源抽象为「类型定义 + 实现」两层，新增源只改实现层、不改消费方
- 抓取设置自适应间隔与缓存，避免被封

---

## 四、研究员/大纲师承载（长文研究写作方法论）

### 4.1 STORM（斯坦福）

**仓库**：https://github.com/stanford-oval/storm （10k+ Star）

**核心方法论**：
- **两阶段生成**：Pre-writing（检索+大纲）→ Writing（分节撰写+引用）
- **多视角提问驱动检索**：从相似主题的已有文章挖掘不同视角来控制提问过程
- **模拟对话追问**：作者 vs 领域专家的对话，基于检索结果更新理解并追问 follow-up question
- **多 LM 分工降本**：便宜模型做对话拆分与提问，强模型做大纲/正文/润色

**对研究员的启示**：
1. 先扫同类爆款提炼多视角
2. 每个视角展开「模拟对话+检索」循环
3. 汇总为分层大纲
4. 分节撰写时每节绑定引用源
5. polish 去重+补总结段
6. **强制要求每个事实陈述带引用源编号**

**对大纲师的启示**：分层大纲生成（Outline Generation Module）

---

### 4.2 Agents' Room（Google DeepMind）

**仓库**：https://github.com/google-deepmind/tell_me_a_story

**核心方法论**：
- **双层分离**：Planning Agents 只写 Scratchpad（中间产物，不进最终输出），Writing Agents 写 Scratchpad + 最终输出
- **Scratchpad 共享黑板 + 标签定位**：有序序列记录所有 agent 输出及标签（`[CHARACTER]`/`[SETTING]`），后续 agent 通过标签引用避免冗余
- **写作 agent 提示铁律**：自然衔接上文、匹配既有文风/词汇/情绪、不重复已述内容、只写本节、不要结尾

**对研究员/大纲师的启示**：
- 大纲师/研究员只产结构化卡片入共享区
- 撰稿人按分节模板写作，强制 `承接上文 + 不重复 + 只写本节`
- 共享区用标签分区（`[选题]`/`[事实]`/`[金句]`/`[结构]`），撰稿人按标签检索引用

**五段式骨架可迁移为新媒体骨架**：
钩子(EXPOSITION) → 铺垫(RISING) → 高潮/观点(CLIMAX) → 收束(FALLING) → 行动号召(RESOLUTION)

---

## 五、秘书承载（多 Agent 编排框架范式）

### 5.1 CrewAI

**仓库**：https://github.com/crewAIInc/crewAI （25k+ Star）

**核心抽象**：
- **Role 三元组**：`role`（角色定位）+ `goal`（目标）+ `backstory`（人设背景）+ `tools` + `LLM`
- **Task 三件套**：`description` + `expected_output`（结构化 schema）+ `agent` + `output_file`
- **Crew vs Flow**：Crew 自主协作（创意环节），Flow 精确控制（发布流水线）
- **串行 process** 自动把上一步输出喂给下一步，`hierarchical` process 注入 manager agent 做协调

**对秘书的启示**：
- 角色卡模板：`role / goal / backstory / tools / llm` 五字段
- 任务卡强制 `expected_output` + `output_file` 结构化交付物
- 创意环节用 sequential crew，发布环节用 flow（带状态管理与条件分支）

---

### 5.2 MetaGPT

**仓库**：https://github.com/geekan/MetaGPT （45k+ Star）

**核心哲学**：`Code = SOP(Team)`——把人类团队 SOP 显式编码

**核心方法论**：
- **SOP 即提示词链**：每个角色只做 SOP 规定的事，避免越界与发散
- **结构化交接产物**：每步产出标准化文档（PRD→设计文档→API 定义→代码），下游 Role 直接消费结构化产物而非自由文本
- **角色专业化 + 流水线串行**：前置产物是后置环节的输入约束

**对秘书/大纲师的启示**：
- 为写作团队定义写作 SOP：选题→研究→大纲→撰稿→审校→排版，每步有准入/准出标准
- 每个环节定义标准化交付物 schema（选题卡/研究简报/大纲 JSON/成稿分段+引用）
- **下游角色只能消费上游的结构化产物，不允许凭空臆造**

---

## 六、方法论语料整合表（写入哪个 Agent）

| Agent | 主要借鉴来源 | 应写入角色卡的方法论要点 |
|---|---|---|
| **秘书** | CrewAI、MetaGPT、newsnow | ① SOP 编排：sequential process 串起全流程，每步有准入/准出标准；② 任务卡强制 `expected_output` + `output_file` 结构化交付物；③ 接入 newsnow MCP server 轮询热点做日程触发，抓取设自适应间隔防封 |
| **选题官** | DailyHot、newsnow、STORM | ① 统一热榜 API 轮询 40+ 平台，按类别筛选去重；② 数据源双层抽象、可插拔；③ 用 STORM「多视角提问」从同类爆款提炼选题角度 |
| **研究员** | STORM、Agents' Room、MetaGPT | ① 多视角提问 + 模拟对话驱动检索；② 产出标准化研究简报 schema，只写 Scratchpad 不写正文；③ 每条事实强制带引用源编号 |
| **大纲师** | STORM、Agents' Room、MetaGPT | ① 分层大纲生成；② 五段式骨架迁移：钩子→铺垫→高潮→收束→行动号召；③ 大纲产物为结构化 JSON 入共享区，下游按标签引用 |
| **撰稿人** | Agents' Room、STORM、MetaGPT | ① 写作提示铁律：承接上文 + 匹配文风 + 不重复已述 + 只写本节 + 不结尾；② 分节撰写时每节绑定引用源；③ 只消费上游结构化产物，禁凭空臆造 |
| **审查员** | humanize-chinese-writing、humanizer（33 模式） | ① 内置 humanize-chinese-writing 五层检查 + 9 类审计风险（已下载本地）；② 参考 humanizer 33 模式检查表（每条配中文 before/after）；③ 四步改写流程：识别→改写→审计 pass→二次改写；④ 事实核查 + 引用源完整性校验 |
| **风格官** | humanizer、doocs/md、humanify | ① Voice Calibration：用作者真实样本分析句式节奏/用词/怪癖后对齐；② 句式多样化 + 个人化语气注入；③ 定义内容样式规范写入主题 CSS |
| **排版师** | doocs/md、mdnice | ① 「Markdown + 主题 CSS」范式，内容与样式彻底分离；② 维护多平台主题 CSS 库 + 每平台适配规则清单；③ 图片统一走图床接口、代码块独立高亮主题 |

---

## 七、本地资源清单

```
tools/
├── downloaded/
│   └── humanize-chinese-writing/   # 已 git clone（--depth 1）
│       ├── README.md                # 回答者惯性理论 + 落笔前四步 + 五层检查
│       ├── SKILL.md                 # Skill 定义文件
│       ├── references/patterns.md   # 中文 AI 味 6 大类模式（结构/信息/句式/节奏/文体/复读）
│       ├── scripts/audit_chinese_ai_style.py  # 机械审计脚本
│       └── agents/openai.yaml        # Codex/OpenAI 元数据
└── references/
    └── methodology.md               # 本文件：10 个项目方法论提炼 + 整合表
```

---

## 八、接入说明

1. **已下载本地**：humanize-chinese-writing（MIT License），审查员可直接读取 `references/patterns.md` 作为五层检查的扩展清单
2. **在线版可用**：doocs/md（https://md.doocs.tech）、mdnice（https://mdnice.com），排版师按需调用
3. **API 形式接入**：DailyHotApi（统一路由 `/weibo`/`/zhihu`/`/36kr`），选题官按需调用
4. **方法论参考**：CrewAI/MetaGPT/STORM/Agents' Room/humanizer 等只吸收设计思路，不下载源码
5. **未来如需扩展**：可参考 `external-skills.md` 优先级速查表选择下一批下载对象

当前版本：v1.0（10 个项目方法论提炼完成，1 个项目已下载本地）
