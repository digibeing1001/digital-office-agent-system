# benchmark-runner — benchmark 运行

## 用途
在标准 benchmark 上运行实验,按官方数据划分和评估口径对比 baseline 与本方法,产出结构化的 benchmark 结果报告,确保对比公平、可对比、可复现。

适用于:标准 benchmark 跑分、baseline 对比、SOTA 验证、跨方法公平对比等场景。

## 触发条件
- 用户要求"跑 benchmark""对比 baseline""在 X 数据集上评估"时。
- 需要在标准数据集上验证本方法效果时。
- 用户提到"benchmark""SOTA""跑分"时。

## 操作步骤
1. **选 benchmark**:根据实验方案选择标准 benchmark,记录每个 benchmark 的任务类型、版本、split。
2. **下载数据**:按官方来源下载数据集,记录数据版本和 hash,不得手工篡改 split。
3. **跑 baseline**:用官方实现或公平复现的 baseline 在同一数据集上跑,记录结果和运行配置。
4. **跑自己的方法**:在本方法上用相同数据、相同评估口径跑,记录结果和运行配置。
5. **记录结果**:每个 benchmark 记录任务名、指标、baseline 值、本方法值、运行次数、均值±标准差。
6. **对比**:按指标方向性判断本方法是否优于 baseline,标注差异是否统计显著。

## 调用示例
```bash
# 跑 baseline
python run_benchmark.py \
  --method baseline \
  --benchmark GLUE \
  --split official \
  --seed 42 \
  --output outputs/baseline_glue/

# 跑本方法
python run_benchmark.py \
  --method ours \
  --benchmark GLUE \
  --split official \
  --seed 42 \
  --output outputs/ours_glue/
```

## 输出格式
benchmark 结果报告,含以下字段:
- 任务名 / benchmark 名 / 版本 / split
- 指标名 / 指标方向性(高好或低好)
- baseline 值(均值±标准差,运行次数)
- 本方法值(均值±标准差,运行次数)
- 差值 / 是否统计显著
- 运行配置(种子 / 硬件 / 超参)

## 约束
- **用 benchmark 官方数据划分和评估口径**:不得自改 split 或自创评估脚本。
- baseline 与本方法必须用相同数据、相同口径,不得偏袒。
- 若 baseline 用原作者报告值,必须标注"未在本环境复现"。
- 本方法不如 baseline 的结果必须如实报告,不得隐藏。
