# 文献检索技能(Literature Retrieval)

## 用途
对指定研究主题进行系统化的学术文献检索,产出可复现的检索证据链、PRISMA 四步筛选记录、引文三重交叉验证结果,以及包含综述、分类法、研究空白报告和 BibTeX 文件的完整文献包。

适用于:开题前文献综述、申报书背景章节、Related Work 撰写、技术调研、研究方向论证、综述论文撰写等场景。

## 触发条件
满足以下任一条件即激活本技能:
- 用户明确要求"检索文献""做文献综述""查相关研究""系统综述""PRISMA 筛选""找 related work"
- 任务需要从多数据库汇聚某主题的学术文献并产出引文清单
- 需要对一批引文做真实性验证(防止幻觉引用)
- 需要识别研究空白(gap analysis)

## 操作步骤

### 步骤 1:确定检索策略
在动笔检索前,先把策略写下来,确保后续可复现。

1. **数据库选型**:按主题领域选择至少 2-3 个互补数据库
   - arXiv API:CS/Physics/Math 预印本,覆盖最新工作
   - Semantic Scholar API:跨学科,带影响力指标和引用图谱
   - OpenAlex API:覆盖最广(2.4 亿+ works),元数据规范
   - Crossref API:DOI 权威来源,用于引文交叉验证
   - 特定领域补充:PubMed(生物医学)、DBLP(计算机)、IEEE Xplore(工程)
2. **关键词组合**:列出核心概念 + 同义词 + 上位词 + 下位词
   - 使用布尔运算符 AND/OR/NOT 组合
   - 记录每组查询的完整 query string
   - 区分"主题词"(controlled vocabulary)与"自由词"(free text)
3. **时间范围**:明确起止年份并说明依据(如"2020 年后因 Transformer 主导该领域")
4. **纳入排除标准**(Inclusion/Exclusion Criteria):
   - 纳入:同行评审论文、预印本、语言(中/英)、最小引用数等
   - 排除:非主题相关、重复发表、无全文、学位论文(视需求)

### 步骤 2:执行检索并记录证据
1. 按既定 query 在每个数据库执行检索
2. **逐次记录**:数据库名 / 查询语句 / 检索日期 / 命中数量 / 返回字段
3. 查询语句必须可直接复制粘贴复用,不得简化或改写
4. 分页拉取全部结果(不要只取首页),记录总条数
5. 原始结果存入中间文件(JSON/CSV),保留 query 元数据

### 步骤 3:PRISMA 四步筛选
按 PRISMA 2020 规范执行,每一步都要记录数量流转:

1. **Identification(识别)**:从各数据库汇总命中总数 N1
   - 去除数据库间重复:N1 → N2(记录去重数量)
2. **Screening(筛选)**:基于标题+摘要初筛
   - 按纳入排除标准剔除明显不相关:N2 → N3
   - 记录每条剔除理由(主题不符/语言不符/类型不符)
3. **Eligibility(资格)**:全文评估
   - 获取 N3 篇全文,逐篇判断是否符合资格:N3 → N4
   - 记录无法获取全文的数量和原因
4. **Inclusion(纳入)**:最终纳入综述的文献 N4
   - 输出 PRISMA flow diagram 的数量表

### 步骤 4:引文三重交叉验证
对每一条最终纳入的文献,通过三个独立来源验证其真实存在性和元数据准确性(综合自 ARS 方法论):

1. **Semantic Scholar 验证**:用 paperId / 标题查询,确认论文存在
2. **OpenAlex 验证**:用 DOI / OpenAlex ID 查询,核对标题/作者/年份/venue
3. **Crossref 验证**:用 DOI 查询 Crossref,核对元数据权威性
4. **三方比对**:标题、作者列表、发表年份、venue 四个字段三方一致 → 标"已验证"
   - 两方一致一方缺失 → 标"部分验证"
   - 三方均查不到 → 标"待验证"并提示人工核查(严禁直接删除或编造)

### 步骤 5:深度阅读与信息抽取
对纳入文献逐篇提取结构化信息:
- 研究问题 / 方法核心 / 数据集 / 主要指标 / 关键结论 / 局限性
- 与本主题的关联点(直接相关 / 方法借鉴 / 对比 baseline)

### 步骤 6:产出综合输出
1. **文献综述**:按主题/方法/时间线组织,呈现研究脉络
2. **分类法**:对纳入文献建立分类标签体系(如按方法类型/应用场景/评估维度)
3. **研究空白报告**:明确指出当前研究的不足、未解决问题、可拓展方向
4. **BibTeX 文件**:输出标准 .bib 文件,每条 entry 附 verification status 字段

## 输出格式
产出以下文件包(建议放在 `outputs/literature/<topic>-<date>/`):
- `search-strategy.md`:检索策略完整记录
- `prisma-flow.md`:PRISMA 四步数量流转 + 剔除理由汇总
- `verification-report.md`:引文三重验证结果表
- `synthesis.md`:文献综述正文
- `taxonomy.md`:分类法
- `gap-report.md`:研究空白报告
- `references.bib`:BibTeX 引用文件(含验证状态)
- `raw-results/`:各数据库原始检索结果

## 约束
- **绝不编造引用**:无法验证的文献必须标注"待验证",不得虚构作者/年份/venue
- **查询可复现**:所有 query 必须原文记录,不得事后改写
- **去重透明**:记录去重依据(DOI / arXiv ID / 标题归一化)
- **数量可追溯**:PRISMA 每步数字必须能从原始结果回推
- **不篡改元数据**:三方来源不一致时,以 Crossref 为权威,差异记入备注
- **语言诚实**:非英文文献不得擅自翻译成英文引用
- **限流遵守**:严格遵守各 API 的 rate limit,失败重试要记录

## 依赖工具/API
- **arXiv API**:预印本检索,`http://export.arxiv.org/api/query`,无 key 需要
- **Semantic Scholar API**:`https://api.semanticscholar.org/graph/v1/`,带影响力字段
- **OpenAlex API**:`https://api.openalex.org/works/`,无需 key 但建议加 mailto 提速
- **Crossref API**:`https://api.crossref.org/works/`,DOI 权威验证
- **可选**:PubMed E-utilities、DBLP API、Unpaywall(获取 OA 全文链接)
- 本地工具:BibTeX 校验器、标题归一化函数、PRISMA flow 生成器

## 关键方法论引用
- PRISMA 2020 筛选规范(Page et al., BMJ 2021)
- ARS 引文三重验证:Semantic Scholar + OpenAlex + Crossref 三源交叉
- 标题归一化:小写 + 去标点 + 去多余空格后比较,避免大小写/标点差异漏去重
