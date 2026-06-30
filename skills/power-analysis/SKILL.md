# power-analysis — 功效分析

## 用途
在实验设计阶段计算所需样本量或实验次数,确保实验有足够统计功效检测真实效应。避免"实验做完了但样本不够,无法得出显著性结论"的窘境。

## 触发条件
- 规划实验需要确定样本量 / 实验次数时。
- 实验结果不显著,需要判断是否因功效不足时。
- 用户提到"样本量""功效""power""显著性"时。

## 工具依赖
```bash
pip install statsmodels numpy
```

## 操作步骤
1. 确定效应量(effect size):基于先验知识或预实验估计期望检测的最小效应。
2. 确定显著性水平 α(通常 0.05)。
3. 确定期望功效 1-β(通常 0.8)。
4. 用 statsmodels 计算所需样本量。
5. 若已有样本,计算当前功效是否达标。

## 调用示例
```python
import numpy as np
from statsmodels.stats import power as smp

# === 场景1:两样本 t 检验,算需要多少样本 ===
# 假设:模型A准确率 0.85,模型B准确率 0.88, pooled std=0.04
mean_a, mean_b, std = 0.85, 0.88, 0.04
effect_size = (mean_b - mean_a) / std  # Cohen's d = 0.75

alpha = 0.05
power = 0.8
ratio = 1.0  # 两组样本量相等

n = smp.tt_ind_solve_power(effect_size=effect_size, alpha=alpha,
                            power=power, ratio=ratio, alternative="larger")
print(f"每组需 {int(np.ceil(n))} 次实验 (effect_size={effect_size:.2f})")

# === 场景2:已知样本量,算功效 ===
actual_n = 10  # 每组做了 10 次
achieved_power = smp.tt_ind_solve_power(effect_size=effect_size, alpha=alpha,
                                         nobs1=actual_n, ratio=1.0,
                                         alternative="larger")
print(f"每组 {actual_n} 次实验的功效: {achieved_power:.3f}")

if achieved_power < 0.8:
    print("⚠️ 功效不足(<0.8),不足以支撑显著性结论,需增加实验次数")

# === 场景3:ANOVA 多组比较 ===
# 3 组,效应量 f=0.25(中等)
n_anova = smp.FTestAnovaPower().solve_power(effect_size=0.25, alpha=0.05,
                                             power=0.8, k_groups=3)
print(f"ANOVA 3 组比较每组需 {int(np.ceil(n_anova))} 样本")
```

## 输出格式
- 所需样本量(每组实验次数)。
- 当前功效值(若已有样本)。
- 效应量、α、power 的参数说明。

## 约束
- 样本不足以达到 0.8 功效时,必须明确说"当前样本量不足以支撑显著性结论",不可含糊。
- 效应量必须基于先验知识或预实验,不可随意假设。
- 功效分析应在实验前做(前瞻性),不可在实验后调整效应量来"凑"显著。
