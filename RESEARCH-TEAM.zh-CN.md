# 科研团队:让 AI 像真正的科研人员一样干活

这个分支给 Digital Office 加了一套"科研团队"。你说一句"我想研究 XXX",后面从查文献、定方向、做实验、写论文到审稿,有一队 AI 角色帮你分工干完。

## 为什么做这个

一个能做科研的人,不是靠"聪明",而是靠**积累**——读过大量论文,做过很多实验,踩过坑,知道什么思路靠谱。我们想让 AI 团队也具备这种积累。

所以这套配置做了三件事:
1. **给每个角色写了灵魂文档**,让 ta 知道自己是谁、该怎么想、什么不能做
2. **给每个角色配了具体工具**,查论文有查论文的工具,画图有画图的工具,查重有查重的工具
3. **给团队配了会自动更新的知识库**,像图书馆一样越用越丰富

## 团队里有谁

一共 10 个角色:

### 一直要在的

| 角色 | 干什么 | 配了什么工具 |
|---|---|---|
| **科研秘书** | 接活、分活、盯进度 | 自动分派(按能力匹配角色)、硬管控审批门 |
| **课题规划师** | 定研究方向、找创新点 | 文献计量分析、STORM 多视角主题探索 |
| **文献研究员** | 查论文、写综述、找空白 | arXiv 检索、Google Scholar 检索、Semantic Scholar 检索、PDF 全文解析(GROBID) |
| **学术写作员** | 写论文、改稿 | LaTeX 工具链、引用自动生成、BibTeX 管理、语法检查、Word/Excel 生成 |

### 看情况叫来帮忙的

| 角色 | 干什么 | 配了什么工具 |
|---|---|---|
| **方法学专家** | 设计实验、选统计方法 | 实验设计模板、因果推断、功效分析 |
| **实现工程师** | 写代码、跑实验 | 实验跟踪(MLflow)、超参调优(Optuna)、配置管理(Hydra)、RL 实验库、可复现包导出、失败实验归档 |
| **数据分析师** | 算数据、画图、核对数字 | 出版级配图(SciencePlots)、复现核对自动化 |
| **质检员** | 模拟审稿人找问题 | 事实核查(FActScore)、逐条 claim 验证、图片完整性检查 |
| **伦理员** | 查重、查合规、查造假 | 代码查重(JPlag)、文本查重(MinHash)、AI 内容检测、图片取证 |

### 后勤

| 角色 | 干什么 | 配了什么工具 |
|---|---|---|
| **资料员** | 定时抓新论文,自动入库 | RSS 聚合、OCR(PaddleOCR)、元数据抽取、四级去重、引文网络、实体抽取 |

## 每个角色的能力从哪来

我们做了两轮调研:

**第一轮:学术论文**。找了 10+ 篇顶会论文,把验证过的方法论写进了每个角色的灵魂文档:
- 课题规划师借鉴了 ResearchAgent(用学术图找创新点)、Co-STORM(多视角圆桌)、斯坦福关于"AI 生成想法容易同质化"的研究
- 文献研究员借鉴了 AutoSurvey(综述四段式)、OpenScholar(每句话追溯到原文)、STORM(多视角提问)
- 质检员借鉴了 DeepReview(多阶段评审)、AgentReview(多角色模拟审稿)、SciFact(逐条验证)
- 方法学专家借鉴了 DS-Agent(案例库复用)、AI Scientist(实验闭环)
- 资料员借鉴了 OpenScholar(证据包)、ResearchAgent(知识图谱)

**第二轮:GitHub 开源工具**。找了 30+ 个开源工具,把每个工具的调用方法写成了技能文件,绑定到对应角色:
- 文献检索:arxiv.py、scholarly、semanticscholar、GROBID
- 实验跟踪:MLflow、Optuna、Hydra、Stable Baselines3
- 数据可视化:SciencePlots、Altair、Plotly、seaborn
- 学术写作:crossrefapi、PyLaTeX、latexify、bibtexparser、Pandoc
- 质量检查:FActScore
- 伦理查重:JPlag、datasketch
- 资料采集:feedparser、PaddleOCR、crossrefapi、habanero、datasketch、NetworkX

另外从 Anthropic 官方 skills 仓库下载了 4 个通用技能放进 `skills/_imported/`:
- **pdf**:PDF 读取、表单填写、OCR
- **skill-creator**:自动生成新技能
- **docx**:Word 文档生成
- **xlsx**:Excel 生成

## 一共多少文件

- 10 个角色,每个有灵魂文档(SOUL.md)+ 配置文件(config.yaml)
- 41 个技能文件(5 个科研流程技能 + 36 个工具型技能 + 4 个官方导入技能)
- 2 份设计文档(知识库设计 + 能力增强说明)

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

### 第三步:角色交接

```
秘书(确认要干啥)
  → 规划师(定方向和创新点)
  → 文献研究员(查论文,写综述,找空白)
  → 方法学专家(设计实验)
  → 实现工程师(写代码,跑实验)
  → 数据分析师(算结果,画图)
  → 写作员(起草论文)
  → 质检员(模拟审稿找问题)
  → 伦理员(查重查合规)
  → 交付
```

每步留痕,能追溯。

## 知识库:越用越聪明

三层知识:
1. **领域知识库**(团队共享):教材、已读论文、实验方案、案例、可复现实验包
2. **项目资料**(单个项目专属):底稿、综述、实验数据、论文草稿
3. **团队规矩**:引用规范、数据诚信、署名规则

知识库不绑死任何工具,支持 Obsidian、Notion、本地文件夹。

资料员每天自动去 arXiv 等信源抓新论文,去重入库打标签,不用手动搜。

## 文件在哪

```
profiles/                        10 个角色
  office-research-secretary/     科研秘书
  office-research-pi/            课题规划师
  office-literature-researcher/  文献研究员
  office-academic-writer/        学术写作员
  office-methodologist/          方法学专家
  office-research-engineer/      实现工程师
  office-data-analyst/           数据分析师
  office-peer-reviewer/          质检员
  office-research-ethics/        伦理员
  office-knowledge-curator/      资料员

skills/                          41 个技能
  literature-retrieval/          文献检索(PRISMA + 三重引文验证)
  experiment-design/             实验设计
  academic-writing/              学术写作
  peer-review/                   同行评审
  knowledge-curation/            资料采集
  mlflow-tracking/               实验跟踪
  optuna-hpo/                    超参调优
  ... (共 36 个工具型技能)
  _imported/                     从 Anthropic 官方导入
    pdf/                         PDF 处理
    skill-creator/               技能生成器
    docx/                        Word 生成
    xlsx/                        Excel 生成

docs/
  knowledge-base-design.md                   知识库设计
  research-team-capability-enhancement.zh-CN.md  工具清单和论文来源
```

## 测试建议

1. 跟秘书说:"我想研究 XXX"
2. 看秘书问不问那几个关键问题
3. 看分派对不对
4. 看每个角色干完活交接时信息全不全
5. 看质检员能不能挑出真问题
6. 看资料员定时采集能不能跑通

不对劲就反馈,我们改。

## 协议说明

所有自写的角色文档和技能文件为原创。推荐安装的 Python 库均为 MIT/Apache/BSD 协议。从 Anthropic 官方导入的 pdf/skill-creator/docx/xlsx 遵循其原协议。论文方法论仅参考借鉴,未复制代码。GPL 工具建议本地使用,不打包再分发。
