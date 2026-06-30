# latex-syntax-check — LaTeX 语法检查

## 用途
LaTeX 文档交稿前的静态语法检查。使用 chktex 检测常见排版问题(未闭合括号、间距错误、标点顺序等),逐条修复直到无错误。

## 触发条件
- LaTeX 论文交稿前。
- 编译报错需要排查语法问题时。
- 用户提到"LaTeX 检查""chktex""语法"时。

## 工具依赖
```bash
# chktex(CLI),通常随 TeX 发行版安装
chktex --version
# 若未安装:
#   Ubuntu: sudo apt install chktex
#   macOS: brew install chktex
```

## 操作步骤
1. 运行 `chktex` 对 `.tex` 文件做静态检查。
2. 解析报告,逐条列出问题(行号、类型、描述)。
3. 逐条修复(括号不匹配、间距、标点顺序等)。
4. 重新运行 chktex,直到无错误。
5. 有错误不交稿。

## 调用示例
```bash
# 基本检查
chktex -v main.tex

# 输出到文件
chktex -q main.tex -o chktex_report.txt

# 常见警告类型:
#   Warning 1:  命令后应加空格
#   Warning 6:  标点前不应有空格
#   Warning 8:  括号不匹配
#   Warning 13: 数学环境外用 $
#   Warning 17: 数字后缺单位
#   Warning 26: 引号方向错误
```

解析报告并批量处理(Python):
```python
import subprocess
import re

def run_chktex(tex_file):
    """运行 chktex 并返回问题列表"""
    result = subprocess.run(
        ["chktex", "-q", "-v0", tex_file],
        capture_output=True, text=True
    )
    issues = []
    for line in result.stdout.strip().split("\n"):
        # 格式: "File:Line:Message"
        match = re.match(r'(.+?):(\d+):\s*(.+)', line)
        if match:
            issues.append({
                "file": match.group(1),
                "line": int(match.group(2)),
                "message": match.group(3).strip(),
            })
    return issues

def fix_common_issues(tex_file):
    """自动修复常见问题"""
    with open(tex_file, encoding="utf-8") as f:
        content = f.read()

    # 修复:命令后缺空格(如 \textbf{前应 \textbf {})
    content = re.sub(r'(\\[a-zA-Z]+)([^{\s])', r'\1 \2', content)
    # 修复:标点前多余空格
    content = re.sub(r'\s+([,.;:!?])', r'\1', content)
    # 修复:左引号应为 `` 而非 "
    content = content.replace('"', '``"', 1)  # 简化,需更精细处理

    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(content)

# 执行检查
issues = run_chktex("main.tex")
print(f"发现 {len(issues)} 个问题:")
for iss in issues:
    print(f"  行 {iss['line']}: {iss['message']}")

# 自动修复常见问题后重检
fix_common_issues("main.tex")
issues2 = run_chktex("main.tex")
print(f"\n修复后剩余 {len(issues2)} 个问题")
if issues2:
    print("⚠️ 仍有问题,需人工修复,不可交稿")
else:
    print("✅ 检查通过")
```

## 输出格式
- chktex 报告(行号、问题类型、描述)。
- 修复后的 `.tex` 文件。

## 约束
- 有错误不交稿,chktex 报告必须清零。
- 自动修复只处理确定性问题,模糊问题需人工判断。
- chktex 之外还需实际编译(pdflatex)确认无编译错误。
