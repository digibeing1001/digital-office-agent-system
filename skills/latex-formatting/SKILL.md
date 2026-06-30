# latex-formatting — LaTeX 排版

## 用途
按目标会议/期刊的官方模板,完成论文 LaTeX 排版:文档结构、章节、公式、表格、图表、参考文献,产出可编译的 LaTeX 源文件和 PDF。

适用于:论文起草完成后的排版环节,或从草稿阶段就用 LaTeX 写作。

## 触发条件
- 论文草稿完成,需要转成会议模板
- 用户指定投稿目标(NeurIPS/ICML/ICLR/ACL/CVPR 等)
- 用户要求"排成 LaTeX""套模板"
- 已有 LaTeX 源文件需要修正编译错误

## 操作步骤

### 步骤 1:选模板
1. 确认目标会议/期刊(必须用户明确指定,不得擅自选)
2. 获取官方模板:
   - NeurIPS: neurips_2024.sty
   - ICML: icml2024.sty
   - ICLR: iclr2024_conference.sty
   - ACL: acl.sty
   - CVPR: cvpr.sty
3. 严格使用官方模板,不用第三方"美化版"
4. 确认页数限制、字号、行距、边距等格式约束

### 步骤 2:生成文档结构
1. 套用模板的 documentclass 和宏包
2. 生成标准章节结构:
   - \title / \author / \affiliation
   - \begin{abstract} ... \end{abstract}
   - \section{Introduction} / \section{Related Work} / \section{Method} / \section{Experiments} / \section{Conclusion}
3. 加载必要宏包:
   - amsmath / amssymb(公式)
   - graphicx(插图)
   - booktabs(表格三线表)
   - hyperref(超链接)
   - natbib / biblatex(引用)
4. 不加载与模板冲突的宏包

### 步骤 3:公式排版
1. 行内公式用 $...$ 或 \(...\)
2. 行间公式用 equation 环境给编号
3. 多行公式用 align / align*(对齐等号)
4. 长公式用 multline 或 split
5. 公式中的符号必须先在正文或符号表定义
6. 编号公式按出现顺序自动编号,引用用 \eqref

### 步骤 4:表格图表插入
1. **表格**:
   - 用 booktabs 的 \toprule / \midrule / \bottomrule(三线表)
   - 不用 \hline(过时且丑)
   - 数值列右对齐,文本列左对齐
   - 最优值 \mathbf 或 \textbf 加粗
   - 表注用 \multicolumn 跨列 + \footnotesize
2. **图表**:
   - 矢量图优先(PDF/SVG),位图 ≥ 300 DPI
   - \includegraphics[width=\linewidth]{figs/xxx.pdf}
   - 图表放 floats 环境(\begin{figure} / \begin{table})
   - \caption 在图下、表上(位置正确)
   - \label 在 \caption 之后,引用用 \ref / \autoref

### 步骤 5:编译检查
1. 运行 pdflatex / xelatex / lualatex 编译(按模板要求)
2. 处理编译错误:
   - Undefined control sequence:宏包没加载
   - Missing $ inserted:公式没闭合
   - Float too large:图表超出版心
3. 处理警告:
   - Overfull \hbox:行宽超出,手动断行
   - Reference undefined:\ref 引用不存在,检查 \label
4. 连续编译 2-3 次(解决交叉引用)
5. BibTeX 编译参考文献:bibtex main && pdflatex main && pdflatex main

## 调用示例
```latex
\documentclass{neurips_2024}
\usepackage{amsmath, amssymb, graphicx, booktabs, hyperref}
\title{LoRA on Long Context: A Systematic Study}
\author{Author Name}
\begin{document}
\maketitle
\begin{abstract}
...
\end{abstract}
\section{Introduction}
...
\begin{equation}
\mathcal{L} = \sum_{i=1}^{N} \ell(f_\theta(x_i), y_i)
\label{eq:loss}
\end{equation}
As shown in Eq.~\eqref{eq:loss}, ...
\begin{table}[t]
\caption{Main results on LongBench.}
\label{tab:main}
\centering
\begin{tabular}{lcc}
\toprule
Method & Accuracy & Latency \\
\midrule
Full FT & 65.2 & 100ms \\
LoRA & 63.8 & 80ms \\
\bottomrule
\end{tabular}
\end{table}
\end{document}
```

## 输出格式
- **LaTeX 源文件**(写入 `outputs/writing/<project>-latex/`):
  - main.tex:主文件
  - sections/*.tex:分章节文件(可选)
  - figs/:图表文件
  - references.bib:参考文献
- **PDF**:编译产物
- **编译日志**:errors.log / warnings.log

## 约束
- 必须用会议官方模板,不用第三方美化版
- 不得为了"好看"擅自改模板的字号/行距/边距
- 公式符号必须先定义再用,不得无定义出现
- 表格用三线表(booktabs),不用 \hline
- 图表 caption 位置:图在下,表在上
- 编译错误必须修复,不得留 Error 提交
- Overfull/Underfull 警告尽量修复,关键页必查
- 投稿前走 approval-routing(论文投稿提交是硬管控)
