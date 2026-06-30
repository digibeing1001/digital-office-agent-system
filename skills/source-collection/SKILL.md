# source-collection — 信源采集

## 用途
从多个信源(RSS / arXiv / Semantic Scholar / OpenAlex)采集文献,做初步过滤后入队待处理,为文献研究员提供持续的文献输入流。

适用于:文献持续采集、新论文监控、信源聚合等场景。

## 触发条件
- 用户要求"采集文献""拉新论文""监控信源"时。
- 需要从多个信源聚合文献时。
- 用户提到"信源采集""source collection""文献采集"时。

## 操作步骤
1. **加载信源列表**:读取信源配置(RSS 订阅源 / arXiv 分类 / S2 检索式 / OpenAlex 查询),明确每个信源的采集方式。
2. **采集**:按信源类型分别采集:
   - RSS:用 feedparser 拉取最新条目。
   - arXiv:用 arXiv API 按分类/关键词检索。
   - Semantic Scholar:用 S2 API 按 paper/author 检索。
   - OpenAlex:用 OpenAlex API 按概念/机构检索。
3. **初步过滤**:按标题/摘要做关键词和语言过滤,剔除明显不相关条目。
4. **入队待处理**:把通过初过滤的文献写入待处理队列,等文献研究员做进一步筛选和分类。

## 调用示例
```python
import feedparser

# RSS 采集
feed = feedparser.parse("https://export.arxiv.org/rss/cs.AI")
for entry in feed.entries:
    print(entry.title, entry.link)

# arXiv API 采集
import arxiv
search = arxiv.Search(query="large language model", max_results=50)
for result in arxiv.Client().results(search):
    print(result.title, result.entry_id)
```

## 输出格式
待处理文献队列,每条含:
- 标题 / 作者 / 摘要 / 来源 / 链接 / 发布时间
- 采集来源(RSS / arXiv / S2 / OpenAlex)
- 采集时间戳

## 约束
- **遵守 robots.txt 和 API 限流**:不得高频请求,按各 API 的 rate limit 设间隔。
- 初过滤只做粗筛,不替代文献研究员的人工筛选。
- 采集到的文献必须记录来源,便于追溯。
- 信源配置变更需记录,便于排查采集异常。
