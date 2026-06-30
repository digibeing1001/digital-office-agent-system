# doe-templates — 实验设计模板

## 用途
基于实验设计(Design of Experiments, DOE)方法学,系统化地规划实验矩阵。支持全因子设计、响应面设计、拉丁超立方采样等,确保实验覆盖参数空间且无遗漏,避免"拍脑袋"式实验。

## 触发条件
- 需要规划一组实验来探索多因素影响时。
- 实验因素≥3 个且存在交互作用时。
- 用户提到"实验设计""DOE""全因子""响应面"时。

## 工具依赖
```bash
pip install pyDOE2 numpy pandas
```

## 操作步骤
1. 明确研究问题,选定因素(factors)和响应(responses)。
2. 选设计类型:
   - 全因子(fullfact):因素少、需分析交互。
   - 响应面(Box-Behnken / CCF):需拟合曲面、找最优。
   - 拉丁超立方(lhs):因素多、计算机实验。
3. 用 pyDOE2 生成设计矩阵。
4. 将设计矩阵记录到 MLflow 或 Excel,标注每组实验编号。
5. 按矩阵逐组实验,记录响应值。

## 调用示例
```python
import numpy as np
import pandas as pd
from pyDOE2 import fullfact, lhs, bbdesign

# === 全因子设计 ===
# 3 因素,水平数 [2, 3, 2],共 2*3*2=12 组
design_full = fullfact([2, 3, 2])
df_full = pd.DataFrame(design_full, columns=["lr_level", "bs_level", "wd_level"])
print("全因子设计:\n", df_full)

# === 拉丁超立方采样 ===
# 4 因素,20 组实验
design_lhs = lhs(4, samples=20, criterion="maximin")
# 归一化到实际范围
lr = 10 ** (-1 - 4 * design_lhs[:, 0])      # 1e-1 ~ 1e-5
bs = (design_lhs[:, 1] * 224 + 32).astype(int)  # 32 ~ 256
wd = design_lhs[:, 2] * 0.1                  # 0 ~ 0.1
dropout = design_lhs[:, 3] * 0.5             # 0 ~ 0.5
df_lhs = pd.DataFrame({"lr": lr, "batch_size": bs,
                        "weight_decay": wd, "dropout": dropout})
print("LHS 设计:\n", df_lhs.head())

# === Box-Behnken 响应面设计(3 因素) ===
design_bb = bbdesign(3)
print(f"Box-Behnken 设计:{len(design_bb)} 组实验")

# 导出实验矩阵
df_lhs.to_csv("doe_design.csv", index=False)
```

## 输出格式
- 实验设计矩阵(CSV/DataFrame),每行一组实验,每列一个因素。
- 记录设计类型、因素数量、实验组数到 MLflow tag。

## 约束
- 设计类型必须对应研究问题:分析交互用全因子,寻优用响应面,高维探索用 LHS。
- 不随意增删实验组,按设计矩阵执行。
- 因素水平映射关系(归一化值→实际值)必须记录,保证可复现。
