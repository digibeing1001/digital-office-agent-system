# code-plagiarism-check — 代码查重

## 用途
对代码类产出做查重,检测是否与已有代码库存在抄袭。使用 JPlag 做基于 token 流的结构化比对,支持多语言,输出相似度报告和疑似抄袭片段。

## 触发条件
- 代码类作业/论文产出需要查重时。
- 怀疑代码存在抄袭时。
- 用户提到"代码查重""plagiarism""JPlag"时。

## 工具依赖
```bash
# JPlag 需要 Java 运行环境
# 下载: https://github.com/jplag/JPlag/releases
# 确保 java -version 可用
java -version
```

## 操作步骤
1. 准备待查代码目录(每份代码一个子目录或文件)。
2. 准备比对库目录(已有代码 / 历年作业 / 开源项目)。
3. 运行 JPlag,指定语言和目录。
4. 解析 JPlag 输出的报告(HTML / JSON)。
5. 对高相似度结果人工复核。

## 调用示例
```bash
# JPlag CLI 命令
# -l 指定语言: java, python3, cpp, csharp, go, kotlin, scala, rust...
# -s 子目录模式(每个提交一个子目录)
jplag \
  -l python3 \
  -r result_report \
  submissions_dir/ \
  -bc base_code_dir/ \
  -t 5 \
  -m 50

# 参数说明:
#   -l python3        检测语言
#   -r result_report  报告输出目录
#   submissions_dir/  待查代码目录
#   -bc base_code_dir 比对基准库(已有代码)
#   -t 5              最小匹配 token 数
#   -m 50             最多显示 50 个匹配
```

解析报告(Python):
```python
import json
import os

# JPlag 输出 result_report/overview.json
with open("result_report/overview.json") as f:
    report = json.load(f)

# 提取高相似度对
for match in report.get("matches", []):
    sub_a = match["submission1"]
    sub_b = match["submission2"]
    similarity = match["similarity"]
    if similarity > 0.4:  # 相似度 > 40% 标红
        print(f"⚠️ {sub_a} vs {sub_b}: {similarity:.1%}")
        print(f"   匹配片段数: {match['matchCount']}")
```

## 输出格式
- JPlag HTML 报告(含高亮疑似抄袭片段)。
- 相似度矩阵 CSV。
- 高相似度对列表(>阈值)。

## 约束
- 多语言支持,按实际语言选 `-l` 参数。
- 比对库必须覆盖主流开源项目和历年产出,否则漏报。
- 查重结果仅作参考,最终判定需人工复核代码结构。
- 代码查重看结构相似度,非逐字符比对。
