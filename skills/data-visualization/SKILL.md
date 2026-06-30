# data-visualization — 数据可视化

## 用途
把实验结果画成可发表的图表,按数据特性选合适的图表类型,配置完整图注,导出高分辨率,并核查坐标轴诚实性,避免误导性绘图。

适用于:论文实验结果图、对比柱状图、收敛曲线、消融对比图、误差棒图等场景。

## 触发条件
- 用户要求"画图""可视化""画结果图"时。
- 论文需要把实验数据画成图表时。
- 用户提到"plot""figure""柱状图""曲线图"时。

## 操作步骤
1. **选图表类型**:按数据特性选(折线图看趋势、柱状图看对比、箱线图看分布、散点图看关系),避免用错类型。
2. **画图**:用 matplotlib / seaborn 画图,加坐标轴标签、单位、图例、误差棒(均值±标准差或置信区间)。
3. **配图注**:为每张图配完整图注(图号 / 描述 / 符号说明 / 误差棒定义 / 数据来源),图注能脱离正文独立理解。
4. **导出高分辨率**:导出矢量格式(PDF / SVG)或高分辨率位图(≥300 dpi),适配期刊要求。
5. **检查坐标轴诚实**:检查 y 轴是否截断放大差异、颜色是否误导、误差棒是否完整、失败组是否保留。

## 调用示例
```python
import matplotlib.pyplot as plt
import seaborn as sns

fig, ax = plt.subplots(figsize=(6, 4))
sns.barplot(x=methods, y=scores, ax=ax, ci=95)
ax.set_ylabel("Accuracy (%)")
ax.set_xlabel("Method")
ax.set_title("Comparison on Benchmark X")
plt.tight_layout()
plt.savefig("fig1_comparison.pdf", dpi=300, bbox_inches="tight")
```

## 输出格式
- 图表文件(PDF / SVG / PNG,≥300 dpi)。
- 图注文本(图号 / 描述 / 符号说明 / 误差棒定义)。
- 作图数据表(可选,供他人复现图表)。

## 约束
- **坐标轴诚实**:不得截断 y 轴放大差异,不得用非线性坐标轴却不标注。
- **失败组保留**:本方法不如 baseline 的结果必须如实画出,不得隐藏。
- 误差棒必须标注是标准差还是置信区间。
- 配色考虑色盲友好,不依赖红绿区分。
