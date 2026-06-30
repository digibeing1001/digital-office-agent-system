# 科研团队能力增强说明

这份文档记录了为每个角色补充能力的调研结果:参考了哪些论文方法论、推荐装哪些开源工具、哪些能直接用、哪些只能参考。

## 一、参考的学术论文(方法论来源)

这些论文的方法论已经融入对应角色的"灵魂文档"(SOUL.md)的"思维方式"部分。

### 跨角色的协作设计

| 论文 | 来源 | 借鉴点 |
|---|---|---|
| The AI Scientist | Sakana AI, arXiv:2408.06292 | 端到端科研流水线(idea→实验→写作→审稿)的参考实现 |
| ResearchAgent | arXiv:2404.07738, NAACL 2025 | 学术图扩展找创新点 + 评审嵌入 idea 迭代环 |
| STORM / Co-STORM | Stanford, arXiv:2402.14207 / 2408.15232 | 多视角 persona 提问发现研究角度 |
| AutoSurvey | arXiv:2406.10252, NeurIPS 2024 | 综述自动生成四段式(检索→大纲→分段起草→评估重写) |
| OpenScholar | Nature 2026 | 每条 claim 必须追溯到原文段落 + 页码 |
| Can LLMs Generate Novel Ideas? | Stanford, arXiv:2409.04109 | LLM 生成 idea 新颖但同质化严重,必须强制多样性 |
| DS-Agent | arXiv:2402.17453, ICML 2024 | 案例库复用(CBR)做自动 ML 实验 |
| DeepReview | arXiv:2503.08569 | 多阶段结构化评审 + 14B 开源评审模型 |
| AgentReview | EMNLP 2024 Oral | 多角色模拟审稿,复现权威偏见和群体思维 |
| SciFact | arXiv:2004.14974 | 科学 claim 验证基准 |

### 每个角色具体借鉴了什么

**课题规划师**:ResearchAgent 的学术图扩展(从核心论文出发拉引用网络找创新点);Si et al. 的多样性约束(每次生成≥5个 idea 分属不同子领域);Co-STORM 的圆桌(理论派/工程派/应用派/批评派相互提问)。

**文献研究员**:AutoSurvey 的四段式(严禁一次性整篇生成);OpenScholar 的 claim 溯源(无溯源的断言直接拒绝);STORM 的多 persona 提问大纲。

**质检员**:DeepReview 的多阶段(结构化分析→逐 claim 检索证据→论证批评→给建议);AgentReview 的多 persona(严格派/宽松派/专家派/批评派各出评审再讨论);SciFact 的 claim 级验证(SUPPORT/REFUTE/证据不足);ResearchAgent 的嵌入式评审(不事后审,而是嵌进 idea 迭代环)。

**方法学专家**:DS-Agent 的 CBR 案例库(新实验先检索相似案例);AI Scientist 的实验闭环(写代码→跑→看结果→调→再跑);因果推断护栏(区分相关性 claim 和因果性 claim)。

**资料员**:三源采集(OpenAlex 元数据 + Semantic Scholar 影响力 + arXiv 最新预印本);OpenScholar 的 evidence pack(存段落级证据包不是论文清单);自动引文网络(NetworkX 存本地引文图);ResearchAgent 的实体库(抽取方法名/数据集名/指标名形成知识图谱)。

## 二、推荐安装的开源工具(按角色)

### 优先级说明
- **P0**:MIT/Apache/BSD 协议,可直接装、可商业用
- **P1**:GPL 协议,本地用可以,不要再打包分发
- **P2**:仅参考方法论,不安装

### 课题规划师(PI)

| 工具 | 协议 | 用途 | 安装 |
|---|---|---|---|
| pybibliometrics | MIT | Python 文献计量 | `pip install pybibliometrics` |
| STORM | MIT | 多角度主题预写作 | `pip install knowledge-storm` |

### 文献研究员

| 工具 | 协议 | 用途 | 安装 |
|---|---|---|---|
| arxiv.py | ISC(≈MIT) | arXiv API 检索 | `pip install arxiv` |
| scholarly | Unlicense | Google Scholar 检索 | `pip install scholarly` |
| semanticscholar | MIT | Semantic Scholar API | `pip install semanticscholar` |
| GROBID | Apache 2.0 | PDF 全文结构化解析 | Docker 部署,见 github.com/kermitt2/grobid |
| pdfplumber | MIT | PDF 表格/元数据抽取 | `pip install pdfplumber` |

### 方法学专家

| 工具 | 协议 | 用途 | 安装 |
|---|---|---|---|
| DoWhy | MIT | 因果推断框架 | `pip install dowhy` |
| EconML | MIT | 异质因果效应 | `pip install econml` |
| pyDOE2 | BSD | 实验设计(全因子/响应面) | `pip install pyDOE2` |
| statsmodels | BSD | 统计建模/假设检验 | `pip install statsmodels` |

### 实现工程师

| 工具 | 协议 | 用途 | 安装 |
|---|---|---|---|
| MLflow | Apache 2.0 | 实验跟踪 | `pip install mlflow` |
| Optuna | MIT | 超参调优 | `pip install optuna` |
| Ray Tune | Apache 2.0 | 分布式超参调优 | `pip install ray[tune]` |
| Hydra | MIT | 配置管理 + 扫参 | `pip install hydra-core` |
| Stable Baselines3 | MIT | RL 算法实现 | `pip install stable-baselines3` |

### 数据分析师

| 工具 | 协议 | 用途 | 安装 |
|---|---|---|---|
| SciencePlots | MIT | Nature/Science/IEEE 风格配图 | `pip install SciencePlots` |
| Altair | BSD-3 | 声明式可视化(出版级) | `pip install altair` |
| Plotly | MIT | 交互式可视化 | `pip install plotly` |
| seaborn | BSD | 统计可视化 | `pip install seaborn` |

### 学术写作员

| 工具 | 协议 | 用途 | 安装 |
|---|---|---|---|
| crossrefapi | BSD | DOI→BibTeX/APA/MLA 自动生成 | `pip install crossrefapi` |
| PyLaTeX | MIT | Python 生成 LaTeX 文档 | `pip install Pylatex` |
| latexify_py | Apache 2.0 | Python 函数→LaTeX 公式 | `pip install latexify` |
| bibtexparser | MIT | .bib 文件读写 | `pip install bibtexparser` |
| Pandoc | GPL-2 | Markdown↔LaTeX↔Word 转换 | 系统安装,CLI 调用 |

### 质检员

| 工具 | 协议 | 用途 | 安装 |
|---|---|---|---|
| FActScore | MIT | 细粒度事实性评分 | `pip install factscore` |

### 伦理员

| 工具 | 协议 | 用途 | 安装 |
|---|---|---|---|
| JPlag | BSD-3 | 代码查重(学术级) | github.com/jplag/JPlag |
| datasketch | MIT | MinHash LSH 文本去重/查重 | `pip install datasketch` |

### 资料员

| 工具 | 协议 | 用途 | 安装 |
|---|---|---|---|
| feedparser | BSD-2 | RSS/Atom 订阅解析 | `pip install feedparser` |
| PaddleOCR | Apache 2.0 | 多语言高精度 OCR | `pip install paddleocr` |
| crossrefapi | BSD | DOI→元数据抽取 | `pip install crossrefapi` |
| habanero | MIT | Crossref/PubMed 多源元数据 | `pip install habanero` |
| datasketch | MIT | MinHash LSH 文档去重 | `pip install datasketch` |

## 三、一键安装所有 P0 工具

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

GROBID 和 JPlag 需要单独部署(Docker/Java),参见各自仓库说明。

## 四、只参考方法论不安装的(P2)

| 项目 | 协议 | 为什么不装 |
|---|---|---|
| bibliometrix | GPL-3 | R 生态,GPL 不可再分发 |
| VOSviewer | CC BY-NC | 非商业,仅参考思路 |
| Marker | GPL-3 | GPL,仅本地参考 |
| Pingouin | GPL-3 | GPL,仅本地参考 |
| ARS(academic-research-skills) | CC BY-NC | 非商业,仅参考方法论不复制代码 |
| AI-Scientist | Apache 2.0 | 代码体量大,抽取其 prompt 思路即可,不整体集成 |
| DetectGPT/Binoculars | 研究代码 | 准确率有限,参考思路自封装 |
| 图片篡改检测(LarryJiang134/MVSS-Net) | 研究代码 | 需工程化,参考方法论 |

## 五、技能缺口(开源生态较弱,需自封装)

调研发现以下几块开源工具不成熟,需要我们参考方法论自己写 skill:

1. **PRISMA 流程图自动生成**:无成熟开源库,引用 PRISMA 2020 规范 + graphviz 自写
2. **商业级文本查重引擎**:Turnitin 闭源;开源用 datasketch MinHash 自建本地引擎
3. **AI 生成内容检测**:开源方案准确率低于商业产品,用 DetectGPT/Binoculars 思路 + 多模型投票,标注"参考性指标"
4. **图片篡改检测**:研究代码需工程化,参考 ELA(误差分析)思路自实现
5. **对话追问方法论/任务排班**:无现成学术 skill,参考 AutoGen/LangGraph Supervisor 模式自封装

## 六、协议合规说明

本配置包所有内容为原创编写,未复制任何 CC BY-NC/GPL 项目的代码与文案。所有借鉴的方法论均已注明论文来源(arXiv ID)。推荐安装的工具均为 MIT/Apache/BSD 协议,可商业使用。GPL 工具仅建议本地使用,不打包进可分发的 skills 目录。
