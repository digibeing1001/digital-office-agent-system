# 资料采集技能(Knowledge Curation)

## 用途
定时从配置的信源采集学术论文,经过主题过滤、去重、规范登记、分类打标后,自动更新知识库并入"新到文献"队列,供文献研究员进一步深度处理。本技能是知识库的"上游入口",保证知识库持续更新且不重复膨胀。

适用于:科研团队日常文献跟踪、研究方向动态监控、知识库自动维护、文献研究员的输入供给等场景。

## 触发条件
满足以下任一条件即激活本技能:
- 用户要求"采集文献""更新知识库""定时抓论文""监控 arXiv""新文献通知"
- 框架的 Schedule 定时任务触发本技能
- 用户配置了新的信源清单,需要立即执行一次采集
- 文献研究员报告"知识库过期",需要补充新鲜文献

## 操作步骤

### 步骤 1:加载信源清单
1. 读取信源配置文件(建议路径:`config/knowledge-sources.yaml`)
2. 信源清单结构示例:
   ```yaml
   sources:
     - name: "arXiv-cs.CL"
       type: "arxiv_api"
       category: "NLP"
       keywords: ["large language model", "retrieval augmented"]
       filters:
         time_range: "last_7_days"
         categories: ["cs.CL"]
       frequency: "daily"
     - name: "SemanticScholar-ML"
       type: "semantic_scholar_api"
       category: "Machine Learning"
       keywords: ["efficient inference"]
       filters:
         min_citations: 5
       frequency: "weekly"
     - name: "HuggingFace-Papers"
       type: "rss"
       url: "https://huggingface.co/papers"
       category: "AI General"
       frequency: "daily"
   ```
3. 按当前时间筛选应执行的信源(对照 frequency:daily / weekly / monthly)
4. 记录本次采集任务覆盖的信源列表

### 步骤 2:执行采集
按信源类型调用对应采集器:

1. **arXiv API 采集器**:
   - 端点:`http://export.arxiv.org/api/query`
   - 构造 query:按 keywords 组合 + categories 过滤
   - 分页拉取(start=0, max_results=100, 逐页递增)
   - 解析 Atom feed,提取:arXiv ID / 标题 / 作者 / 摘要 / 分类 / 发布日期 / PDF 链接
   - **限流**:arXiv 建议 ≥3 秒间隔,单次查询 ≤1000 条
2. **Semantic Scholar API 采集器**:
   - 端点:`https://api.semanticscholar.org/graph/v1/paper/search`
   - 参数:query + fields(title,authors,year,venue,citationCount,externalIds,abstract)
   - 分页:offset + limit
   - **限流**:无 key 100 req/5min;有 key 1 req/sec
3. **OpenAlex API 采集器**:
   - 端点:`https://api.openalex.org/works`
   - 参数:search + filter(publication_year, type, concepts)
   - 建议 mailto 参数提升速率(polite pool)
   - **限流**:10 req/sec(polite pool),否则 2 req/sec
4. **RSS 采集器**:
   - 解析 RSS/Atom feed
   - 提取:title / link / pubDate / description
   - 适用于:HuggingFace Papers / Reddit r/MachineLearning / 特定博客
5. **指定页面采集器**(慎用):
   - 仅当无 API 时使用
   - 严格遵守 robots.txt
   - 解析 HTML 提取论文信息

### 步骤 3:主题过滤
1. 按信源配置的 keywords 做相关性初筛
   - 标题或摘要包含任一 keyword → 通过初筛
   - 支持正则匹配(高级配置)
2. 按排除词清单剔除(如:"survey of surveys" / 明显不相关的子领域)
3. 可选:调用 LLM 做语义相关性判断(关键词匹配不足时)
   - prompt:"判断这篇论文是否与 [主题] 相关,返回 yes/no + 理由"
4. 通过初筛的进入下一步;未通过的记录"主题不相关"并跳过

### 步骤 4:去重
1. **去重依据**(按优先级):
   - DOI 最权威(若存在)
   - arXiv ID(若存在)
   - 标题归一化匹配(小写 + 去标点 + 去多余空格 + 去停用词后比较)
2. 三级去重流程:
   - 第一级:本次采集批次内部去重
   - 第二级:与知识库已有文献去重(查 DOI / arXiv ID)
   - 第三级:与"待确认"队列去重(标题相似度 > 0.95 视为重复)
3. 去重时若发现同一论文来自不同信源,合并元数据(取最完整的)
4. 记录每条去重决策的依据

### 步骤 5:规范登记
对每篇入库文献登记以下字段(完整规范):

```
title:          论文标题(原文,不翻译)
authors:        作者列表(按原顺序,姓-名格式)
year:           发表年份
venue:          发表场所(journal/conference/preprint)
doi:            DOI(若有)
arxiv_id:       arXiv ID(若有)
openalex_id:    OpenAlex ID(若有)
semantic_scholar_id: Semantic Scholar paperId(若有)
category_tags:  分类标签(对齐文献研究员分类法)
core_contribution: 一句话核心贡献摘要
abstract:       摘要原文
pdf_path:       本地 PDF 路径(若已下载)
source_urls:    各来源链接
acquisition_time: 采集时间
acquisition_source: 采集信源
verification_status: 已验证 / 部分验证 / 待验证
relevance_score: 相关性评分(0-1)
status:         new / in_review / curated / archived
```

### 步骤 6:打分类标签
1. 加载文献研究员维护的分类法(从知识库读取 `taxonomy.json`)
2. 对每篇论文按其内容打标签:
   - 主题标签:如 NLP / CV / RL / Systems
   - 方法标签:如 Transformer / Diffusion / Retrieval-Augmented
   - 应用标签:如 Translation / Generation / Classification
3. 自动打标策略:
   - 基于摘要的关键词匹配(快速但粗糙)
   - 基于分类号的映射(arXiv cs.CL → NLP)
   - 可选:LLM 辅助打标(精确但有成本)
4. 无法确定分类的,标 `uncategorized` 并入"待确认"队列
5. 标签冲突时(一篇论文可属多类),允许多标签

### 步骤 7:记录采集日志
每次采集任务完成后,记录结构化日志:

```
acquisition_log:
  task_id: <uuid>
  start_time: <timestamp>
  end_time: <timestamp>
  sources_covered: ["arXiv-cs.CL", "SemanticScholar-ML"]
  sources_failed: [{name: "HuggingFace-Papers", reason: "RSS timeout"}]
  total_hits: 245
  after_topic_filter: 120
  after_dedup: 78
  newly_inserted: 45
  duplicates_skipped: 33
  irrelevant_skipped: 125
  pending_confirmation: 12
  errors: [...]
```

日志存入 `logs/acquisition/<date>.log`,供后续审计和调优。

### 步骤 8:通知与入队
1. 新入库的文献加入"新到文献"队列(知识库中的 `inbox` 表)
2. 触发通知:
   - 若配置了文献研究员 agent,向其发送"新到 N 篇,待处理"
   - 若有重要作者/主题的新论文(配置 watchlist),立即通知
3. "待确认"队列中的文献,定期汇总给文献研究员人工判断
4. 通知方式遵循框架的通知机制(邮件 / IM / 框架内消息)

## 输出格式
产出以下内容(建议路径 `outputs/curation/<date>/`):
- `acquired-papers.jsonl`:本次采集的文献清单(每行一篇,含完整登记字段)
- `dedup-report.md`:去重报告(去重数量 + 依据)
- `acquisition-log.json`:结构化采集日志
- `pending-confirmation.jsonl`:待确认相关性/分类的文献
- `notifications.md`:本次触发的通知列表

知识库更新:
- 写入知识库 `papers` 表(新增条目)
- 写入知识库 `inbox` 队列(待文献研究员处理)
- 更新知识库 `taxonomy` 索引

## 约束
- **遵守 robots.txt**:页面采集前必须检查 robots.txt,不允许的不得强抓
- **遵守 API 限流**:严格按各 API 的 rate limit,失败重试要带退避
- **信源不可用要记录**:不得假装成功,失败要记入日志并通知
- **无法确认相关性的**:入库但标"待确认",不得擅自丢弃或强行分类
- **不篡改元数据**:作者/标题/年份按原始来源记录,不得"美化"
- **不下载非公开 PDF**:只下载 OA 或有权访问的 PDF,版权敏感的只存元数据
- **去重不误杀**:相似度处于模糊区间(0.85-0.95)的,标"疑似重复"待人工确认
- **日志要完整**:每条决策(采集/过滤/去重/分类)都要可追溯
- **不重复采集**:已入库的文献不重新采集(除非用户要求 refresh)

## 依赖工具/API
- **arXiv API**:`http://export.arxiv.org/api/query`,无 key,需 ≥3s 间隔
- **Semantic Scholar API**:`https://api.semanticscholar.org/graph/v1/`,可选 API key
- **OpenAlex API**:`https://api.openalex.org/works`,建议 mailto 进 polite pool
- **RSS 解析**:feedparser(Python)或 rss-parser(Node)
- **HTML 解析**(慎用):BeautifulSoup / cheerio
- **去重工具**:标题归一化函数 + 相似度计算(fuzzywuzzy / rapidfuzz)
- **LLM 辅助**(可选):用于语义相关性判断和自动打标
- **存储**:知识库(SQLite / PostgreSQL / JSON 文件)
- **调度**:框架的 Schedule 工具(定时触发本技能)

## 与框架 Schedule 的配合
本技能设计为可被框架的 Schedule 定时任务调用:

1. **每日采集**(推荐配置):
   - cron: `0 8 * * *`(每天 08:00)
   - 覆盖 frequency=daily 的信源
2. **每周采集**:
   - cron: `0 8 * * 1`(每周一 08:00)
   - 覆盖 frequency=weekly 的信源
3. **每月汇总**:
   - cron: `0 8 1 * *`(每月 1 号 08:00)
   - 汇总上月采集情况,生成月报

调度配置示例(框架 Schedule):
```
action: create
name: "daily-curation"
cron_expression: "0 8 * * *"
timezone: "Asia/Shanghai"
message: "执行每日文献采集任务,加载 config/knowledge-sources.yaml 中 frequency=daily 的信源,调用 knowledge-curation 技能完成采集,完成后通知文献研究员。"
```

## 关键方法论引用
- arXiv API 使用规范(3 秒间隔,User-Agent 标识)
- OpenAlex Polite Pool(mailto 参数提升速率)
- DOI 作为去重黄金标准(Crossref 推荐)
- 标题归一化方法(小写 + 去标点 + 去停用词)
- PRISMA 识别阶段的去重逻辑(本技能复用)
- 知识库增量更新模式(避免全量重抓)
