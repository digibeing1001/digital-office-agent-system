# publication-plotting — 出版级配图

## 用途
生成论文级、期刊级的高质量图表。支持 Nature / Science / IEEE 等期刊风格,图注独立可读,导出高分辨率矢量图,确保图表诚实表达数据。

## 触发条件
- 论文/报告需要正式配图时。
- 用户提到"出版级图表""论文配图""Nature 风格"时。
- 需要导出可投稿的高分辨率图时。

## 工具依赖
```bash
pip install SciencePlots matplotlib seaborn altair plotly
# SciencePlots 需要 LaTeX 环境(可选,用于更精细排版)
```

## 操作步骤
1. 选风格:Nature / Science / IEEE / SciencePlots 预设。
2. 画图:matplotlib + seaborn 静态图,altair / plotly 交互图。
3. 配图注:标题、坐标轴、单位、图例必须独立可读(不看正文也能懂)。
4. 导出:矢量 PDF/SVG + 高分辨率 PNG(300dpi)。
5. 检查:坐标轴诚实、不截断 y 轴、失败组保留、误差线标注。

## 调用示例
```python
import matplotlib.pyplot as plt
import scienceplots  # 注册 science 风格
import numpy as np

# 应用 Nature 风格
plt.style.use(["science", "nature", "no-latex"])

fig, ax = plt.subplots(figsize=(3.5, 2.5))  # Nature 单栏宽度

epochs = np.arange(1, 101)
acc_ours = 1 - np.exp(-epochs / 30) + np.random.randn(100) * 0.01
acc_baseline = 1 - np.exp(-epochs / 50) + np.random.randn(100) * 0.01
acc_failed = 0.3 + 0.001 * epochs + np.random.randn(100) * 0.02  # 失败组

ax.plot(epochs, acc_ours, label="Ours", color="#0173B2")
ax.plot(epochs, acc_baseline, label="Baseline", color="#DE8F05")
ax.plot(epochs, acc_failed, label="Failed ablation", color="#CA0020", linestyle="--")
# 失败组保留,不删除

ax.set_xlabel("Epoch")
ax.set_ylabel("Accuracy")
ax.set_title("Training Accuracy Comparison")
ax.legend(frameon=False)
ax.set_ylim(0, 1.05)  # 不截断 y 轴

fig.tight_layout()
fig.savefig("fig_accuracy.pdf", dpi=300, bbox_inches="tight")  # 矢量
fig.savefig("fig_accuracy.png", dpi=300, bbox_inches="tight")  # 高分辨率
```

Altair 交互图:
```python
import altair as alt
import pandas as pd

df = pd.DataFrame({"epoch": epochs,
                   "accuracy": acc_ours,
                   "method": "Ours"})
chart = alt.Chart(df).mark_line().encode(
    x="epoch:Q", y="accuracy:Q", color="method:N"
).properties(width=400, height=200)
chart.save("interactive_chart.html")
```

## 输出格式
- 矢量图(`.pdf` / `.svg`)。
- 高分辨率位图(`.png`, ≥300dpi)。
- 交互图(`.html`)。

## 约束
- 坐标轴诚实,不截断 y 轴误导读者。
- 失败组(消融实验中表现差的)必须保留在图中,不可删除。
- 误差线必须标注(标准差或置信区间),并在图注说明。
- 图注独立可读,不依赖正文。
