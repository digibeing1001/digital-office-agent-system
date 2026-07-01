# rss-aggregation — RSS 聚合

## 用途
RSS/Atom 订阅源的解析和聚合。从多个 RSS 源拉取最新条目,按关键词/来源过滤后入队,实现文献、博客、新闻的自动化跟踪。

## 触发条件
- 需要订阅和跟踪多个信息源(RSS/Atom)时。
- 用户提到"RSS""订阅""feed""聚合"时。
- 需要定时拉取最新文献/资讯时。

## 工具依赖
```bash
pip install feedparser
```

## 操作步骤
1. 维护 RSS 源列表(`feeds.yaml`,含名称和 URL)。
2. 用 feedparser 解析每个源。
3. 提取条目(标题、链接、摘要、发布时间)。
4. 按关键词/来源/时间过滤。
5. 去重后入队(交由后续流程处理)。
6. 遵守 robots.txt,控制拉取频率。

## 调用示例
`feeds.yaml`:
```yaml
feeds:
  - name: arxiv-cs-CL
    url: "http://export.arxiv.org/rss/cs.CL"
  - name: openai-blog
    url: "https://openai.com/blog/rss.xml"
  - name: hackernews
    url: "https://hnrss.org/frontpage"
```

```python
import feedparser
import yaml
from datetime import datetime, timedelta

def load_feeds(config_path="feeds.yaml"):
    with open(config_path) as f:
        return yaml.safe_load(f)["feeds"]

def fetch_entries(feed_url, since_days=7):
    """解析 RSS,返回最近 N 天的条目"""
    feed = feedparser.parse(feed_url)
    cutoff = datetime.now() - timedelta(days=since_days)
    entries = []
    for entry in feed.entries:
        published = entry.get("published_parsed", entry.get("updated_parsed"))
        if published:
            pub_dt = datetime(*published[:6])
            if pub_dt < cutoff:
                continue
        entries.append({
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "summary": entry.get("summary", "")[:200],
            "source": feed.feed.get("title", ""),
            "published": str(published[:6]) if published else "",
        })
    return entries

def filter_entries(entries, keywords=None):
    """按关键词过滤"""
    if not keywords:
        return entries
    result = []
    for e in entries:
        text = (e["title"] + " " + e["summary"]).lower()
        if any(kw.lower() in text for kw in keywords):
            result.append(e)
    return result

# 执行聚合
feeds = load_feeds()
keywords = ["LLM", "reasoning", "agent"]

all_entries = []
for feed in feeds:
    entries = fetch_entries(feed["url"], since_days=3)
    filtered = filter_entries(entries, keywords)
    all_entries.extend(filtered)
    print(f"{feed['name']}: {len(entries)} 条,过滤后 {len(filtered)} 条")

# 去重(按 link)
seen = set()
unique = []
for e in all_entries:
    if e["link"] not in seen:
        seen.add(e["link"])
        unique.append(e)

print(f"\n聚合结果: {len(unique)} 条(去重后)")
for e in unique[:5]:
    print(f"  - {e['title'][:60]}")
```

## 输出格式
- 条目列表(每条含标题、链接、摘要、来源、发布时间)。
- 去重后的聚合结果。

## 约束
- 遵守 robots.txt,不恶意高频拉取。
- 拉取频率合理控制(建议≥30 分钟一次)。
- 去重按链接 URL,避免重复入队。
