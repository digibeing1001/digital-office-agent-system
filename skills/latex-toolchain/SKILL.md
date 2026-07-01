# latex-toolchain — LaTeX 工具链

## 用途
LaTeX 文档的程序化生成和公式转换。公式用 latexify_py 从 Python 函数自动生成,文档结构用 PyLaTeX 生成,多格式转换用 Pandoc,避免手写公式出错。

## 触发条件
- 需要程序化生成 LaTeX 文档时。
- 需要把 Python 函数转成 LaTeX 公式时。
- 需要 LaTeX 与其他格式(Markdown/Word/HTML)互转时。
- 用户提到"LaTeX""公式生成""Pandoc"时。

## 工具依赖
```bash
pip install pylatex latexify-py
# Pandoc(CLI):https://pandoc.org/installing.html
pandoc --version
```

## 操作步骤
1. 公式:用 `latexify` 从 Python 函数生成 LaTeX 公式,不手写。
2. 文档:用 PyLaTeX 生成 `.tex` 文档(段落、公式、表格、图)。
3. 转换:用 Pandoc 在 LaTeX / Markdown / Word / HTML 间转换。
4. 编译:`pdflatex` 或 `xelatex` 生成 PDF。

## 调用示例
```python
import latexify

# === 1. 公式生成 ===
@latexify.function
def softmax(x, i):
    return math.exp(x[i]) / sum(math.exp(x[j]) for j in range(len(x)))

print(softmax)  # 输出 LaTeX 公式
# \mathrm{softmax}(x, i) = \frac{e^{x_i}}{\sum_{j=0}^{\operatorname{len}(x)-1} e^{x_j}}

@latexify.function
def cross_entropy(y, p, n):
    return -sum(y[i] * math.log(p[i]) for i in range(n))

print(cross_entropy)

# === 2. 文档生成 ===
from pylatex import Document, Section, Math, Figure, Table, Tabular
from pylatex.utils import italic

doc = Document("report", documentclass="article")

with doc.create(Section("Introduction")):
    doc.append("This paper presents a novel approach to ")
    doc.append(italic("machine learning") + ".")

with doc.create(Section("Method")):
    doc.append("The softmax function is defined as:")
    doc.append(Math(data=[softmax]))  # 插入 latexify 生成的公式

with doc.create(Section("Results")):
    with doc.create(Table(position="h!")) as table:
        table.append(Tabular("|c|c|c|"))
        table.add_hline()
        table.append_row(["Method", "Accuracy", "F1"])
        table.add_hline()
        table.append_row(["Ours", "0.92", "0.89"])
        table.add_hline()

doc.generate_pdf(clean_tex=False)
doc.generate_tex()

# === 3. 格式转换(Pandoc) ===
import subprocess

# LaTeX → Markdown
subprocess.run(["pandoc", "report.tex", "-o", "report.md"])
# LaTeX → Word
subprocess.run(["pandoc", "report.tex", "-o", "report.docx"])
# Markdown → LaTeX
subprocess.run(["pandoc", "input.md", "-o", "output.tex",
                "--mathjax", "--standalone"])
```

## 输出格式
- LaTeX 公式字符串。
- `.tex` 文档文件。
- PDF / Word / Markdown(通过 Pandoc 转换)。

## 约束
- 公式不手写,统一用 latexify 从 Python 函数生成,避免符号错误。
- 文档结构用 PyLaTeX 程序化生成,不手写 `.tex` 骨架。
- Pandoc 转换后需检查公式是否正确渲染。
