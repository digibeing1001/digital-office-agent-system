# 科研团队:让 AI 像真正的科研人员一样干活

这个分支给 Digital Office 加了一套"科研团队"。你说一句"我想研究 XXX",后面从查文献、定方向、做实验、写论文到审稿,有一队 AI 角色帮你分工干完。每个角色干完活会被评分,做得不好会带反思返工,跑完会把经验沉淀下来,下次不犯同样的错。

## 这套东西是干什么的

做科研最难的不是"聪明",而是**积累**——读过大量论文、做过很多实验、踩过坑,知道什么思路靠谱。我们想让 AI 团队也具备这种积累。

所以这套配置做了四件事:
1. **给每个角色写了灵魂文档**,让 ta 知道自己是谁、该怎么想、什么不能做
2. **给每个角色配了具体工具和流程技能**,查论文有查论文的工具,画图有画图的工具,查重有查重的工具
3. **给团队加了六维评分卡**,做得好不好有客观标准,不靠 AI 自己说"我做完了"
4. **给团队加了反思进化闭环**,做得不好能返工,返工能反思,跑完能沉淀经验,下次带着经验干活

## 团队里有谁

一共 10 个角色,分三类:

### 一直要在的

| 角色 | 干什么 | 配了什么能力 |
|---|---|---|
| **科研秘书** | 接活、分活、盯进度、评分验收 | 项目接活、风险评分、审批路由、自动分派、硬管控审批门、六维评分卡 |
| **课题规划师** | 定研究方向、找创新点 | 研究问题结构化、假设构建、创新点定位、路线图规划、里程碑跟踪、文献计量、STORM 多视角 |
| **文献研究员** | 查论文、写综述、找空白 | PRISMA 筛选、分类法建设、引文验证、空白识别、arXiv/Scholar/S2 检索、PDF 全文解析 |
| **学术写作员** | 写论文、改稿 | LaTeX 排版、图注规范、体裁切换、引用整合、摘要压缩、引用生成、BibTeX 管理、语法检查 |

### 看情况叫来帮忙的

| 角色 | 干什么 | 配了什么能力 |
|---|---|---|
| **方法学专家** | 设计实验、选统计方法 | 统计方法选择、指标定义、可复现性规划、公平性审查、实验设计模板、因果推断、功效分析 |
| **实现工程师** | 写代码、跑实验 | 实验脚本、版本管理、benchmark 运行、可复现包封装、MLflow 跟踪、Optuna 调优、RL 实验库、失败归档 |
| **数据分析师** | 算数据、画图、核对数字 | 统计建模、显著性检验、数据可视化、异常值检测、出版级配图、复现核对 |
| **质检员** | 模拟审稿人找问题 | 审稿模拟、方法学批评、claim 校准、逻辑一致性检查、可复现性评估、事实核查、图片检查 |
| **伦理员** | 查重、查合规、查造假 | 查重、署名验证、数据合规、IRB 审查、利益冲突、不端检测、LLM 声明、AI 检测、图片取证 |

### 后勤

| 角色 | 干什么 | 配了什么能力 |
|---|---|---|
| **资料员** | 定时抓新论文,自动入库 | 信源采集、分类标签、采集日志、RSS 聚合、OCR、元数据抽取、去重、引文网络、实体抽取 |

## 评分机制:怎么保证产出质量

这是这套系统最核心的设计。AI 自评会高估自己(论文已证实),所以我们不靠 AI 自己说"我做完了",而是有一套六维评分卡。

### 六维评分,满分 100,合格 75

| 维度 | 权重 | 评什么 | 怎么核查 | 一票否决 |
|---|---|---|---|---|
| **严谨性** | 25 | 方法对不对、实验够不够、引用真不真 | 工具核查引用真实性、可复现性、统计显著性 | 是 |
| **新颖性** | 20 | 跟已有工作有没有区别 | 跟近 2 年文献比对 | 是 |
| **清晰度** | 20 | 写得清不清楚、图表规不规范 | 语法检查、格式检查 | 否 |
| **可行性** | 15 | 资源/时间/数据够不够 | 资源评估 | 是 |
| **影响力** | 10 | 问题值不值得做 | — | 否 |
| **置信度** | 10 | 评分者自己有多确信 | — | 否 |

**一票否决**:严谨性、新颖性、可行性这三项,任何一项低于 50%,即使总分过 75 也直接打回返工。

**评分对象**:评分卡只评两类关键产出——PI 的研究蓝图/idea、写作员的论文初稿。其他角色产出(文献综述、实验日志、数据图表、采集报告)走风险分,不用评分卡。

**评分依据**:NeurIPS/ICLR/ACL 顶会审稿标准 + 斯坦福 100+ NLP 研究者的 idea 评估方法(Si et al. 2024) + Sakana AI 的 AI-Scientist 自动评审。

## 循环工程:做得不好能返工,返工能进化

这是让团队"越用越聪明"的关键。不是跑完一次就结束,而是每次跑完都把经验沉淀下来。

### 场景一:评分不合格 → 带反思返工

```
评分不合格
  → 先生成反思("这次哪里不够、为什么不够、下次怎么改")
  → 带着反思重写(不是简单重跑)
  → 重写后重新评分
  → 同一问题连续返工 2 次 → 升级为"不要再犯"的教训,存入经验库
```

最多返工 3 轮,超了上报用户决策。

### 场景二:用户纠正 → 记住不再犯

用户说"以后查文献不要只用 Google Scholar":
- 判断是通用偏好 → 写进这个角色的灵魂文档,以后永远遵守
- 判断是一次性指正 → 只存当前项目,不污染长期记忆
- 不确定时 → 问用户"这是以后都这样,还是就这次"

### 场景三:项目跑完 → 沉淀经验

```
项目结束
  → 回顾整个过程,抽取经验("遇到 X 情况,应该/不应该 Y")
  → 去重后存入经验库
  → 下一个项目启动时,按主题检索 top-5 经验,带着经验干活
```

### 单次反思 vs 跨项目经验

| | 单次反思 | 跨项目经验 |
|---|---|---|
| 存哪 | 当前项目记忆 | 经验库(永久) |
| 例子 | "这次第 2 步检索漏了 X" | "做综述时先查 survey 再查原文" |
| 触发 | 每次返工自动触发 | 项目结束/用户纠正时触发 |

两者都做,不是二选一。

## 角色协作链路

每个角色干完活,按交接契约交给下一个角色。链路闭环:

```
秘书(确认要干啥,生成项目底稿)
  → 规划师(定方向和创新点)
  → 文献研究员(查论文,写综述,找空白,建分类法)
  → 方法学专家(设计实验,定指标)
  → 实现工程师(写代码,跑实验)
  → 数据分析师(算结果,画图)
  → 写作员(起草论文)
  → 质检员(模拟审稿找问题)
  → 伦理员(查重查合规)
  → 交付
```

每步都评分或风险分,不达标返工,返工带反思,跑完沉淀经验。

关键交接点都有明确契约:
- 秘书→PI:项目底稿全文 + 研究类型 + 预算 + 资料库引用
- 文献→方法学:baseline 清单 + 复现要点 + 评估口径参考
- 资料员→PI:实体库(资料员建,PI 消费)
- 质检→伦理:造假信号(质检扫描,伦理深入核查)

## 每个角色的能力从哪来

我们做了三轮调研 + 一轮全局 review 修补:

**第一轮:学术论文**。找了 10+ 篇顶会论文,把验证过的方法论写进了每个角色的灵魂文档:
- 课题规划师借鉴了 ResearchAgent(用学术图找创新点)、Co-STORM(多视角圆桌)
- 文献研究员借鉴了 AutoSurvey(综述四段式)、OpenScholar(每句话追溯到原文)
- 质检员借鉴了 DeepReview(多阶段评审)、AgentReview(多角色模拟审稿)
- 方法学专家借鉴了 DS-Agent(案例库复用)、AI Scientist(实验闭环)

**第二轮:GitHub 开源工具**。找了 30+ 个开源工具,把每个工具的调用方法写成了技能文件:
- 文献检索:arxiv.py、scholarly、semanticscholar、GROBID
- 实验跟踪:MLflow、Optuna、Hydra、Stable Baselines3
- 数据可视化:SciencePlots、Altair、Plotly
- 学术写作:crossrefapi、PyLaTeX、latexify、bibtexparser
- 质量检查:FActScore
- 伦理查重:JPlag、datasketch
- 资料采集:feedparser、PaddleOCR、NetworkX

**第三轮:反思进化机制**。找了 Reflexion、ExpeL、Self-Refine、CRITIC 等论文,给每个角色加了"被评分→反思→返工→沉淀经验→下次进化"的闭环。

**第四轮:全局 review 修补**。对全部配置做了一次全局审查,修了:
- 秘书补齐了评分卡使用章节(六维评分怎么用、什么时候用)
- 补齐了 3 处交接断点(秘书→PI、文献→方法学、资料员→PI)
- 明确了 6 处角色边界冲突(分类法归属、实体库归属、造假检测分工、Related Work 分工、评估维度边界)
- 修了 5 个 Bug(技能名格式错误、self-reflection 字段契约、dedup-engine 丢数据、fact-check API 不匹配)
- 补齐了 44 个角色核心能力技能(原本只在 config 里绑了名,没创建技能文件)

## 这套系统能帮科研人员做什么

### 好处一:不用从零开始查文献
文献研究员配了 arXiv、Google Scholar、Semantic Scholar 三个检索工具,加上 GROBID 解析 PDF 全文,能帮你把相关文献全梳理一遍,每条结论都追溯到原文。

### 好处二:实验设计站得住脚
方法学专家配了因果推断(DoWhy)、实验设计模板(pyDOE2)、功效分析(statsmodels),保证你的实验有对照、有统计显著性、样本量够。

### 好处三:实验可复现
实现工程师配了 MLflow 记录每次实验,Optuna 调超参,自动导出可复现包(git commit + 依赖 + 配置 + 种子),别人照着能跑出一样的数字。

### 好处四:发布前先模拟审稿
质检员用 DeepReview 的多阶段评审,把论文拆成一条条 claim 逐个验证,像顶会审稿人一样找问题。伦理员用 JPlag 查代码查重,用 MinHash 查文本查重。

### 好处五:团队越用越聪明
每次跑完都把经验沉淀下来,下次不犯同样的错。你纠正过的错误,ta 会记住不再犯。

### 好处六:知识库自动更新
资料员每天自动去 arXiv 等信源抓新论文,去重入库打标签,不用你手动搜。

### 好处七:产出质量有客观标准
六维评分卡 + 一票否决,保证严谨性、新颖性、可行性这三项任何一项不达标都打回返工,不靠"感觉"判断好坏。

## 怎么用

### 第一步:装工具

大部分工具是 Python 库,一条命令装完:

```bash
pip install arxiv scholarly semanticscholar pdfplumber \
            dowhy econml pyDOE2 statsmodels \
            mlflow optuna hydra-core stable-baselines3 \
            SciencePlots altair plotly seaborn \
            crossrefapi Pylatex latexify bibtexparser \
            factscore \
            feedparser paddleocr habanero datasketch \
            pybibliometrics knowledge-storm
```

GROBID(PDF 解析)和 JPlag(代码查重)需要单独装,看各自 GitHub 仓库说明。

### 第二步:跟秘书说一句话

比如:"我想研究 AI 记忆框架"

秘书会先问你:
- 要写综述、提新方法、还是复现别人的?
- 给谁看?验收标准是什么?
- 有没有硬限制(必须用国产模型?预算?截止日期?)
- 手头有没有已读的论文或草稿?

答完就分给对应角色开干。

## 文件在哪

```
profiles/                        10 个角色
  office-research-secretary/     科研秘书(含评分卡配置 scoring_config.yaml)
  office-research-pi/            课题规划师
  office-literature-researcher/  文献研究员
  office-academic-writer/        学术写作员
  office-methodologist/          方法学专家
  office-research-engineer/      实现工程师
  office-data-analyst/           数据分析师
  office-peer-reviewer/          质检员
  office-research-ethics/        伦理员
  office-knowledge-curator/      资料员

skills/                          94 个技能
  # 5 个核心科研流程技能
  literature-retrieval/          文献检索(PRISMA + 三重引文验证)
  experiment-design/             实验设计
  academic-writing/              学术写作
  peer-review/                   同行评审
  knowledge-curation/            资料采集

  # 44 个角色核心能力技能
  project-intake/                项目接活
  research-question-structuring/ 研究问题结构化
  prisma-screening/              PRISMA 筛选
  latex-formatting/              LaTeX 排版
  statistical-method-selection/  统计方法选择
  experiment-scripting/          实验脚本
  review-simulation/             审稿模拟
  plagiarism-check/              查重
  source-collection/             信源采集
  ... (共 44 个,每个角色 3-7 个)

  # 36 个工具型技能
  mlflow-tracking/               实验跟踪
  optuna-hpo/                    超参调优
  arxiv-search/                  arXiv 检索
  pdf-parsing/                   PDF 解析
  causal-inference/              因果推断
  fact-check/                    事实核查
  publication-plotting/          出版级配图
  text-plagiarism-check/         文本查重
  ... (共 36 个)

  # 5 个反思进化技能
  research-scoring/              科研评分卡(六维 + 一票否决)
  self-reflection/               反思环(Reflexion 式)
  experience-extraction/         经验抽取(ExpeL 式)
  preference-internalization/    用户纠正内化
  cross-run-memory/              跨项目经验检索

  # 4 个 Anthropic 官方导入技能
  _imported/pdf/                 PDF 处理
  _imported/docx/                Word 生成
  _imported/xlsx/                Excel 生成
  _imported/skill-creator/       技能生成器

docs/
  knowledge-base-design.md                   知识库设计
  research-team-capability-enhancement.zh-CN.md  工具清单和论文来源
  research-scoring-and-reflection.md         评分和反思进化机制详解
```

## 测试建议

1. 跟秘书说:"我想研究 XXX"
2. 看秘书问不问那几个关键问题
3. 看分派对不对
4. 看每个角色干完活交接时信息全不全
5. 看评分卡能不能挑出真问题(不是走过场)
6. 看评分不合格时会不会带反思返工
7. 看项目跑完后会不会沉淀经验
8. 看资料员定时采集能不能跑通

不对劲就反馈,我们改。

## 协议说明

所有自写的角色文档和技能文件为原创。推荐安装的 Python 库均为 MIT/Apache/BSD 协议。从 Anthropic 官方导入的 pdf/skill-creator/docx/xlsx 遵循其原协议。论文方法论仅参考借鉴,未复制代码。GPL 工具建议本地使用,不打包再分发。
