# reproduction-verification — 复现核对自动化

## 用途
复现已有研究时,逐数字核对复现结果与原论文报告值,自动标红超出容忍度的差异,生成结构化核对报告。杜绝"差不多就行"的近似复现。

## 触发条件
- 复现他人论文的实验结果时。
- 需要声明"已复现某工作"之前。
- 用户提到"复现核对""reproduction""逐项对比"时。

## 工具依赖
无额外依赖:
```bash
pip install pandas pyyaml
```

## 操作步骤
1. 整理原论文报告的指标数字(表格/正文),录入 `reference.json`。
2. 运行复现实验,导出你的结果到 `reproduced.json`。
3. 逐项配对同名指标,计算绝对误差和相对误差。
4. 超出容忍度(默认相对误差 >5%)的标红。
5. 生成核对报告,列出匹配项、差异项、无法对应项。

## 调用示例
```python
import json
import pandas as pd

# 原论文报告值
reference = {
    "datasetA": {"accuracy": 0.892, "f1": 0.881, "latency_ms": 12.3},
    "datasetB": {"accuracy": 0.915, "f1": 0.907, "latency_ms": 11.8},
}

# 你的复现结果
reproduced = {
    "datasetA": {"accuracy": 0.889, "f1": 0.875, "latency_ms": 12.9},
    "datasetB": {"accuracy": 0.911, "f1": 0.902, "latency_ms": 12.1},
}

TOLERANCE = 0.05  # 相对误差容忍度 5%

rows = []
for dataset in reference:
    for metric in reference[dataset]:
        ref_val = reference[dataset][metric]
        rep_val = reproduced.get(dataset, {}).get(metric, None)
        if rep_val is None:
            rows.append({"dataset": dataset, "metric": metric,
                         "reference": ref_val, "reproduced": "N/A",
                         "rel_error": "N/A", "status": "MISSING"})
            continue
        abs_err = abs(rep_val - ref_val)
        rel_err = abs_err / abs(ref_val) if ref_val != 0 else float("inf")
        status = "PASS" if rel_err <= TOLERANCE else "FAIL"
        rows.append({"dataset": dataset, "metric": metric,
                     "reference": ref_val, "reproduced": rep_val,
                     "rel_error": f"{rel_err:.4f}", "status": status})

df = pd.DataFrame(rows)
print(df.to_string(index=False))

failed = df[df["status"] == "FAIL"]
if len(failed) > 0:
    print(f"\n⚠️ {len(failed)} 项指标超出容忍度,不可声称完全复现")
else:
    print("\n✅ 全部指标在容忍度内,复现成功")

df.to_csv("reproduction_report.csv", index=False)
```

## 输出格式
- 核对报告 CSV/Markdown 表格,含每项指标的:参考值、复现值、相对误差、状态(PASS/FAIL/MISSING)。
- 汇总:匹配数、失败数、缺失数。

## 约束
- 不近似匹配就声称复现成功,必须逐数字核对。
- 容忍度需提前设定并说明依据(如 ±5%),不可事后调容忍度来"凑"通过。
- 缺失指标标 MISSING,不可省略。
- 有任何 FAIL 项,只能声称"部分复现",不可声称"完全复现"。
