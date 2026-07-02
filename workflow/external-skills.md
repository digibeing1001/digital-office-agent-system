# 外部技能接入索引

> 第三方/外部技能清单（v2.1 版本，含 GitHub 全面调研结果 + 下载状态标注）。
> 接入而非复制代码，按各自许可证约束使用。按承载角色分组。
> 完整方法论提炼见 [tools/references/methodology.md](../tools/references/methodology.md)。

---

## 一、审查员承载（去 AI 味核心）

### humanize-chinese-writing ⭐ 已下载本地
- **仓库**：https://github.com/Lanqingsong/humanize-chinese-writing
- **本地路径**：[tools/downloaded/humanize-chinese-writing/](../tools/downloaded/humanize-chinese-writing/)（MIT License，--depth 1 clone）
- **用途**：中文去 AI 味核心方法论
- **核心理论**：「回答者惯性」——AI 把聊天里的确认、纠正、补充、总结、邀约姿态带进成品
- **方法论**：落笔前先做四步（确定文本任务/建立作者站位/选择组织原则/写出检查首稿）+ 五层检查（站位/结构/信息/句式/节奏）
- **关键文件**：
  - `README.md` —— 回答者惯性理论 + 落笔前四步 + 五层检查方法论
  - `references/patterns.md` —— 中文 AI 味 6 大类模式（结构/信息/句式/节奏/文体/复读）
  - `scripts/audit_chinese_ai_style.py` —— 机械审计脚本，识别 9 类风险
- **使用方式**：审查员可直接读取 `references/patterns.md` 作为五层检查的扩展清单；可执行 `python tools/downloaded/humanize-chinese-writing/scripts/audit_chinese_ai_style.py {file}` 做长文交付前机械审计
- **承载角色**：审查员（[05-reviewer.md](../agents/05-reviewer.md)）
- **边界**：不承诺绕过 AIGC 检测，不靠错别字/病句制造人味

### blader/humanizer
- **仓库**：https://github.com/blader/humanizer （约 33k+ Star）
- **用途**：英文 AI 写作 **33 模式**检查表（实际为 33 个模式，非 24 个，按 5 类组织：内容/语言/风格/交流/填充对冲）
- **方法论提炼**：见 [tools/references/methodology.md](../tools/references/methodology.md) §1.2（含完整 33 模式清单）
- **改写流程**：识别 → 改写 → "obviously AI generated" 审计 → 二次改写
- **承载角色**：审查员（参考，需做中文适配）

### humanify
- **仓库**：https://github.com/PiaoXiaoTian/humanify（抓取失败，疑似不存在或私有）
- **用途**：AI 生成文本改写为更自然人类表达，句式多样化+添加个人化语气词
- **方法论提炼**：见 [tools/references/methodology.md](../tools/references/methodology.md) §1.3（方向性策略，待用户核实仓库地址后补充原文）
- **承载角色**：风格官（参考，已深化进 [06-style-profile.md](../agents/06-style-profile.md) § humanify 策略补充，与 humanize-chinese-writing 互补）

### AI-Text-Humanizer
- **仓库**：社区多个同名项目（100-500 Star 不等）
- **用途**：同义词替换、句式重构、口语化注入降低 AI 检测分数
- **承载角色**：审查员（谨慎参考，提取策略清单补充到去 AI 味规则库）

---

## 二、排版师承载（公众号/多平台排版）

### doocs/md（强烈推荐下载）
- **仓库**：https://github.com/doocs/md （约 9k+ Star，Gitee 镜像 https://gitee.com/Doocs/md）
- **用途**：Markdown→微信公众号图文渲染，实时预览，自定义主题，多图床，AI 助手
- **在线版**：https://md.doocs.tech
- **承载角色**：排版师（公众号出口）
- **集成方式**：抽取核心转换逻辑作为排版师底层引擎，或参考其主题 CSS 设计公众号样式库

### mdnice 墨滴（强烈推荐下载或参考）
- **仓库**：https://github.com/mdnice/markdown-nice （约 4k+ Star）
- **官网**：https://mdnice.com ｜ https://product.mdnice.com
- **用途**：多平台排版（公众号/知乎/掘金/CSDN），30+ 主题，一键排版，免费图床，数学公式
- **承载角色**：排版师（多平台出口，尤其知乎）
- **CLI 版**：https://github.com/zkqiang/mdnice-cli （约 200+ Star）

### wechat-format
- **仓库**：https://github.com/lyricat/wechat-format （约 4k+ Star）
- **用途**：Markdown→公众号格式，行内样式渲染（解决公众号不支持外部 CSS）
- **承载角色**：排版师（备选，比 doocs/md 更轻量）

### blog-auto-publishing-tools
- **仓库**：https://github.com/ddean2009/blog-auto-publishing-tools （约 1k+ Star）
- **用途**：浏览器自动化发布到知乎/简书/博客园/公众号/CSDN（Chrome/Firefox）
- **承载角色**：排版师（发布参考，最终发布保留人工确认）
- **注意**：需注意各平台服务条款合规性

### wechat2markdown
- **仓库**：https://github.com/phodal/wechat2markdown （多个版本，100-500 Star）
- **用途**：公众号历史文章反向转换（公众号→Markdown），便于二次编辑
- **承载角色**：排版师（可选，改写历史文章时用）

---

## 三、选题官承载（热点雷达）

### DailyHot / DailyHotApi 今日热榜（API 形式接入）
- **正确仓库**：
  - 前端：https://github.com/imsyy/DailyHot
  - API：https://github.com/imsyy/DailyHotApi
- **用途**：聚合 40+ 平台热搜榜单（微博/知乎/抖音/B站/百度/头条/36氪/虎嗅/少数派等）
- **完整平台列表**：见 [tools/references/methodology.md](../tools/references/methodology.md) §3.1
- **调用方式**：统一路由 `/{调用名称}`（如 `/weibo`、`/zhihu`、`/36kr`），支持 RSS + JSON 双模式
- **承载角色**：选题官
- **集成方式**：每日定时拉取生成选题池，作为选题官"热点雷达"数据源；按类别（热搜榜/热榜/推荐/快讯）筛选去重

### newsnow
- **仓库**：https://github.com/ourongxing/newsnow （约 3k+ Star）
- **用途**：聚合多平台热点，UI 更现代，支持自定义数据源
- **承载角色**：选题官
- **备注**：比 DailyHot 更新更活跃，可替代或补充

### aihot
- **仓库**：https://github.com/aihubix/aihot （100-500 Star）
- **用途**：AI 圈/科技圈热点聚合
- **承载角色**：选题官
- **备注**：团队定位科技/AI 垂直领域时价值更高

---

## 四、研究员/审查员承载（事实核查）

### fact-check（FactCheck）
- **仓库**：https://github.com/FactCheck/factcheck-tool （200-800 Star）
- **用途**：对文章事实性声明核查，给出可信度评分与证据链接
- **承载角色**：审查员
- **集成方式**：在四层自检之外增加"事实核查"层，特别针对研究员引用的数据/案例

### Source-Verification-Tool
- **仓库**：https://github.com/zhangxiangxin/Source-Verification-Tool （100+ Star）
- **用途**：自动搜索来源链接，验证引用真实性
- **承载角色**：研究员/审查员
- **集成方式**：强化研究员交付材料时的"链接溯源"环节

---

## 五、风格官承载（风格画像/迁移）

### writing-style-skill（ECC 体系内）
- **来源**：ECC 内部 skill（非独立 GitHub 项目）
- **用途**：从样本语料抽取写作风格画像（句长、用词偏好、节奏、口头禅），输出可复用 prompt
- **承载角色**：风格官
- **集成方式**：风格官新建"作者人设"时调用，快速生成该作者的写作指纹

### style-transfer
- **仓库**：https://github.com/mLxL/Style-Transfer 或 https://github.com/fastnlp/style-chen （500+ Star）
- **用途**：文本风格迁移（如"科技风→故事风"），适合不同平台风格切换
- **承载角色**：风格官
- **集成方式**：知乎（深度长文）↔小红书（口语短文）↔公众号（中性叙事）间切换时调用

### Chinese-Simple-Text-Classifier
- **仓库**：https://github.com/zhaoxuhui/Chinese-Simple-Text-Classifier （1k+ Star）
- **用途**：中文文本风格分类建模（新闻/散文/科技等）
- **承载角色**：风格官
- **集成方式**：训练"风格指纹"分类器，识别"是否像 AI 味文本"

---

## 六、秘书承载（多 Agent 框架参考）

### CrewAI
- **仓库**：https://github.com/crewAIInc/crewAI （约 25k+ Star）
- **借鉴**：Role/Task/Crew 抽象可直接迁移到 TEAM.md 的角色卡设计，Research Analyst→Content Writer→Editor 串行交接
- **承载角色**：秘书

### LangGraph
- **仓库**：https://github.com/langchain-ai/langgraph （约 10k+ Star）
- **借鉴**：StateGraph 状态控制，支持审校→打回→重写回路（图结构状态机）
- **承载角色**：秘书

### MetaGPT
- **仓库**：https://github.com/geekan/MetaGPT （约 45k+ Star）
- **借鉴**：SOP 驱动 + 结构化交接产物（PRD→设计文档），中文社区维护活跃
- **承载角色**：秘书/大纲师

### STORM（斯坦福）
- **仓库**：https://github.com/stanford-oval/storm （约 10k+ Star）
- **借鉴**：多角度提问驱动检索→大纲→分节撰写，研究-写作分离，专攻长文
- **承载角色**：研究员/大纲师

### AutoGen
- **仓库**：https://github.com/microsoft/autogen （约 35k+ Star）
- **借鉴**：Agent 间对话式协作（一个 Agent 调用另一个 Agent）
- **承载角色**：秘书

### Agents' Room（Google DeepMind）
- **仓库**：https://github.com/google-deepmind/tell_me_a_story （约 1k+ Star）
- **借鉴**：Planning Agents（只写 Scratchpad）+ Writing Agents（落正文）双层分离
- **承载角色**：秘书

### agent-harness-construction（ECC 体系内）
- **来源**：ECC 内部 skill
- **用途**：优化 Agent 的工具调用空间与提示词设计，提升整体完成率
- **承载角色**：秘书

---

## 七、通用中文 NLP（辅助多角色）

### HanLP
- **仓库**：https://github.com/hankcs/HanLP （约 33k+ Star）
- **用途**：中文分词/词性标注/依存分析/关键词抽取
- **承载角色**：风格官/审查员
- **集成方式**：让风格官做"句长分布统计""虚词频率分析"等量化指标

### jieba
- **仓库**：https://github.com/fxsjy/jieba （约 33k+ Star）
- **用途**：轻量中文分词，关键词提取
- **承载角色**：选题官/研究员
- **集成方式**：选题聚类和标签生成

### ChineseNLPCorpus
- **仓库**：https://github.com/SophonPlus/ChineseNlpCorpus （约 5k+ Star）
- **用途**：中文语料库
- **承载角色**：风格官
- **集成方式**：若后续做"作者风格指纹"机器学习建模，可作为训练数据源

---

## 八、知识库 / 笔记

### getnote（得到大脑 / Get笔记）
- **本地 skill**：`C:\Users\zexin\.trae-cn\skills\getnote\SKILL.md`
- **Base URL**：https://openapi.biji.com
- **认证**：`GETNOTE_API_KEY` + `GETNOTE_CLIENT_ID`（未配置运行 `/note config`）
- **用途**：调研复用、成果沉淀知识库、博主订阅
- **承载角色**：研究员（[02-researcher.md](../agents/02-researcher.md)）
- **集成**：调研前搜索已有笔记、调研中保存有价值信息、调研后打标签归入知识库
- **权限**：note.content.read / note.content.write / note.recall.read

---

## 九、参考：头部博主开源 Skill

### 卡兹克风格创作 Skill
- **来源**：卡兹克开源（GitHub 7.7k Star）
- **用途**：禁用清单 + 四层自检 + 开头/收尾/金句技法
- **承载**：已吸收进 [style-library/kenny-writer.md](../style-library/kenny-writer.md)

---

## 十、QA 框架承载（LLM 评估 / 风格指纹 / 防回归）

> 本节为 v2.2 新增，对应 [qa-framework.md](qa-framework.md) v1.1 的 13 个方法论吸收。
> 这些工具均为 Python/PyTorch/Node 项目，与团队 Markdown-only 架构不直接匹配，登记为「方法论参考，按需下载」。

### DeepEval（方法论参考，按需下载）
- **仓库**：https://github.com/confident-ai/deepeval （约 7k+ Star）
- **用途**：pytest 风格 LLM 评估框架，14+ 内置指标（faithfulness / answer relevancy / context relevancy / hallucination 等），支持 CI/CD 集成
- **承载角色**：审查员（QA 框架第一层方法论参考）
- **对应吸收**：吸收 1 LLM-as-judge 偏见消除 / 吸收 2 FActScore 原子化核查 / 吸收 4 Evals 可演进
- **集成方式**：方法论参考——审查员四层金字塔审查可借鉴其指标设计思想。如团队后续引入代码工程化，可下载集成做自动化评估
- **边界**：Python 项目，需 pytest 环境；当前团队 Markdown-only 架构不直接下载

### StyleLLM（方法论参考，按需下载）
- **仓库**：https://github.com/mbzuaiacademic/StyleLLM （约 1k+ Star）
- **用途**：中文文风学习与迁移，把"风格"从主观感受量化为可计算的指纹（句长分布/虚词频率/标点偏好/语义模式）
- **承载角色**：风格官（QA 框架第三层方法论参考）
- **对应吸收**：吸收 11 风格指纹量化
- **集成方式**：方法论参考——风格官的 9 维画像 + Voice Calibration 机械扫描清单（已在 [06-style-profile.md](../agents/06-style-profile.md) v2.0 落地）是其思想的手工落地。如需自动化指纹计算，可下载集成
- **边界**：PyTorch 项目，需 GPU 环境；当前团队手工量化已满足需求

### Promptfoo（方法论参考，按需下载）
- **仓库**：https://github.com/promptfoo/promptfoo （约 5k+ Star）
- **用途**：CI/CD 防 prompt 回归，改 prompt 时自动跑评估矩阵对比前后
- **承载角色**：审查员 / 秘书（QA 框架第一层方法论参考）
- **对应吸收**：吸收 4 Evals 可演进
- **集成方式**：方法论参考——审查员改 prompt 时可借鉴其评估矩阵思想，防止"修了 A 味、坏了事实性"。如团队后续引入 CI/CD，可下载集成
- **边界**：Node.js CLI 工具；当前团队无 CI/CD 流水线，登记为参考

---

## 接入原则

1. 外部技能按各自许可证约束使用，登记为「本地可用」不代表忽略原作者许可证
2. 不复制大段代码，吸收方法论与清单
3. getnote 需配置环境变量，未配置时提示用户
4. 自动化发布保留人工确认，规避平台合规风险
5. 标注为"参考"的项目不一定要直接下载代码，可阅读其 README/源码吸收设计思路

---

## 优先级速查

| 优先级 | 项目 | 承载角色 | 状态 | 备注 |
|---|---|---|---|---|
| **P0 必备** | humanize-chinese-writing | 审查员 | ✅ 已下载本地 | 中文去 AI 味核心方法论 |
| **P0 必备** | doocs/md | 排版师 | 🌐 在线版可用 | https://md.doocs.tech 公众号排版事实标准 |
| **P0 必备** | mdnice | 排版师 | 🌐 在线版可用 | https://mdnice.com 多平台排版 |
| **P0 必备** | DailyHotApi | 选题官 | 🔌 API 接入 | 40+ 平台热榜，统一路由调用 |
| **P0 必备** | newsnow | 选题官 | 📚 方法论参考 | MCP server 接入思路 |
| **P0 必备** | taste-skill | 风格官 / 排版师 / 审查员 | 📚 引用状态（referenced） | Anti-AI Slop 14 子技能，视觉层去 AI 味，与文本层 humanize-chinese-writing 互补 |
| **P1 强烈推荐** | CrewAI | 秘书 | 📚 方法论参考 | Role/Task/Crew 抽象 |
| **P1 强烈推荐** | MetaGPT | 秘书/大纲师 | 📚 方法论参考 | SOP 驱动 + 结构化交接 |
| **P1 强烈推荐** | STORM | 研究员/大纲师 | 📚 方法论参考 | 多视角提问 + 分节撰写 |
| **P1 强烈推荐** | Agents' Room | 秘书/大纲师/撰稿人 | 📚 方法论参考 | Planning/Writing 双层分离 |
| **P1 强烈推荐** | blader/humanizer | 审查员 | 📚 方法论参考 | 33 模式检查表（英文参考） |
| **P1 强烈推荐** | HanLP/jieba | 风格官/审查员/选题官 | 📚 方法论参考 | 中文 NLP 基础设施 |
| **P2 可选参考** | humanify | 风格官 | ⚠️ 仓库不可访问 | 方向性策略已提炼，已深化进 06-style-profile.md |
| **P2 可选参考** | LangGraph、AutoGen | 秘书 | 📚 方法论参考 | 多 Agent 框架参考 |
| **P2 可选参考** | fact-check、Source-Verification-Tool | 审查员/研究员 | 📚 方法论参考 | 事实核查 |
| **P2 可选参考** | style-transfer、Chinese-Simple-Text-Classifier | 风格官 | 📚 方法论参考 | 风格迁移 |
| **P2 可选参考** | blog-auto-publishing-tools | 排版师 | 📚 方法论参考 | 自动发布参考 |
| **P2 可选参考** | DeepEval | 审查员 | 📚 方法论参考 | LLM 评估框架，对应 QA 框架吸收 1/2/4 |
| **P2 可选参考** | StyleLLM | 风格官 | 📚 方法论参考 | 中文文风量化，对应 QA 框架吸收 11 |
| **P2 可选参考** | Promptfoo | 审查员/秘书 | 📚 方法论参考 | CI/CD 防 prompt 回归，对应 QA 框架吸收 4 |

**状态图例**：✅ 已下载本地 ｜ 🌐 在线版可用 ｜ 🔌 API 接入 ｜ 📚 方法论参考 ｜ ⚠️ 不可访问

---

## 本地资源清单

```
tools/
├── downloaded/
│   └── humanize-chinese-writing/   # P0 已下载（git clone --depth 1）
│       ├── README.md                # 回答者惯性理论 + 落笔前四步 + 五层检查
│       ├── SKILL.md                 # Skill 定义文件
│       ├── references/patterns.md   # 中文 AI 味 6 大类模式
│       └── scripts/audit_chinese_ai_style.py  # 机械审计脚本
└── references/
    └── methodology.md               # 10 个项目方法论提炼 + 整合表
```

---

## 接入说明

1. **已下载本地**（humanize-chinese-writing）：MIT License，审查员可直接读取 `references/patterns.md`
2. **在线版可用**（doocs/md、mdnice）：排版师按需调用，无需下载源码
3. **API 形式接入**（DailyHotApi）：选题官按需调用统一路由
4. **方法论参考**（CrewAI/MetaGPT/STORM/Agents' Room/humanizer 等）：只吸收设计思路，方法论提炼见 `tools/references/methodology.md`
5. **不可访问**（humanify）：建议用户核实仓库地址后补充

---

## 附录：taste-skill 接入说明

> 来源：main 分支 `skills/_imported/taste-skill/`（cross-learning 2026-07）。
> 定位：Anti-AI Slop（反 AI 糟粕）技能族，14 个子技能覆盖前端设计品味 / 输出风格 / 图像生成三条线。
> 与本团队去 AI 味策略的关系：本团队已有的 humanize-chinese-writing（中文去 AI 味）+ humanizer 33 模式（英文参考）聚焦「文本层去 AI 味」；taste-skill 聚焦「视觉与产品层去 AI 味」，两者互补，不重叠。

### taste-skill 14 个子技能概览

**前端设计品味线（10 个）**：

| 子技能 | 用途 | 承载角色 |
|---|---|---|
| design-taste-frontend v2 | 前端设计品味基准 | 风格官 / 排版师（参考） |
| gpt-taste | 通用设计品味校准 | 风格官（参考） |
| image-to-code | 设计稿转代码 | 排版师（参考） |
| redesign | 重新设计 / 视觉重构 | 排版师（参考） |
| soft-skill | 柔和风格调优 | 风格官（参考） |
| output-skill | 输出风格控制 | 风格官（参考） |
| minimalist-skill | 极简主义风格 | 风格官（参考） |
| brutalist-skill | 粗野主义风格 | 风格官（参考） |
| stitch-skill | 多素材缝合 | 排版师（参考） |
| taste-skill-v1 | 基础品味技能 | 风格官（参考） |

**图像生成线（3 个）**：

| 子技能 | 用途 | 承载角色 |
|---|---|---|
| imagegen-frontend-web | Web 端图像生成 | 排版师（参考） |
| imagegen-frontend-mobile | 移动端图像生成 | 排版师（参考） |
| brandkit | 品牌素材包 | 风格官（参考） |

**设置拨盘（Settings Dials）**：

| 拨盘 | 含义 | 建议默认 |
|---|---|---|
| `DESIGN_VARIANCE` | 设计变化度 | 中（避免过度花哨） |
| `MOTION_INTENSITY` | 动效强度 | 低（公众号以静态为主） |
| `VISUAL_DENSITY` | 视觉密度 | 中（平衡信息量与留白） |

### 接入方式

- **引用状态（referenced）**：本团队是 Markdown-only 架构，不直接下载 taste-skill 代码；登记为「方法论参考」，由风格官 / 排版师在需要视觉决策时读取其 README 吸收设计原则。
- **触发场景**：排版师做多平台排版（公众号头图 / 知乎配图）时参考 imagegen 系列的视觉风格指引；风格官做品牌一致性校准时参考 brandkit。
- **边界**：taste-skill 不替代本团队的文本去 AI 味核心 humanize-chinese-writing；两者职责正交，文本层归审查员，视觉层归风格官 / 排版师。

---

当前版本：v2.3（v2.2 基础上新增 taste-skill 条目【P0 必备 · 引用状态】+ 附录「taste-skill 接入说明」含 14 子技能概览 + 3 设置拨盘，吸收自 main 分支 skills/_imported/taste-skill/，cross-learning 2026-07）
