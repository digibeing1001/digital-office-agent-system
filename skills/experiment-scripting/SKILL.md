# experiment-scripting — 实验脚本编写

## 用途
按实验方案编写可复现的实验脚本,将实验设计文档转化为可执行的代码,包含核心逻辑、日志记录和异常处理,确保实验过程可追溯、结果可复现。

适用于:论文实验代码实现、benchmark 跑分脚本、消融研究代码、对比实验脚本等场景。

## 触发条件
- 用户要求"写实验脚本""跑实验""实现实验代码"时。
- 实验方案已确定,需要转化为可执行代码时。
- 用户提到"experiment script""跑 baseline""跑 ablation"时。

## 操作步骤
1. **读实验方案**:读取 experiment-design 产出的方案,明确指标、baseline、ablation 配置、数据划分。
2. **搭实验框架**:建立项目目录结构(config / data / model / train / eval / logs),配置随机种子入口。
3. **实现核心逻辑**:按方案实现数据加载、模型、训练循环、评估指标计算,指标定义与方案一致。
4. **加日志记录**:每个实验运行记录配置、超参、数据版本、指标结果到日志文件(建议接 mlflow-tracking)。
5. **加异常处理**:对数据缺失、OOM、NaN 损失等常见故障加捕获和明确报错,不静默吞错。
6. **测试运行**:用小数据子集做一次 smoke test,确认流水线跑通再上全量。

## 调用示例
```bash
# 固定种子跑一次实验
python run_experiment.py \
  --config configs/exp_main.yaml \
  --seed 42 \
  --output outputs/exp_main_seed42/
```
```python
# 脚本入口固定种子
import random, numpy as np, torch
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
```

## 输出格式
- 实验脚本文件(config / model / train / eval 模块)。
- 运行说明(README 或脚本 docstring):含环境、依赖、运行命令、预期输出。
- 日志文件:记录配置、超参、指标结果。

## 约束
- **脚本必须可复现**:固定随机种子,记录软件版本和硬件环境。
- 指标定义不得与实验方案偏离,偏离必须说明原因。
- 不静默吞错,异常必须抛出或记日志。
- 跑全量前必须先过 smoke test。
