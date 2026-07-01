# optuna-hpo — Optuna 超参调优

## 用途
自动化超参数搜索,替代手动 grid search / random search。使用 TPE(Tree-structured Parzen Estimator)等贝叶斯优化算法高效探索超参空间,并将每次 trial 的结果自动记录到 MLflow。

## 触发条件
- 需要搜索模型超参数(学习率、层数、正则系数等)时。
- 用户提到"调参""超参搜索""HPO""Optuna"时。
- 手动 grid search 成本过高时。

## 工具依赖
```bash
pip install optuna hydra-core mlflow
```

## 操作步骤
1. 定义 `objective(trial)` 函数,内部用 `trial.suggest_*` 采样超参。
2. 在 objective 内训练模型并返回验证指标。
3. 创建 `optuna.create_study(direction="maximize")`。
4. 调用 `study.optimize(objective, n_trials=100)` 启动搜索。
5. 用 `study.best_params` 取最优超参。
6. 用 `MLflowCallback` 把每个 trial 记录到 MLflow,便于对比。

## 调用示例
```python
import optuna
from optuna.integration.mlflow import MLflowCallback

def objective(trial: optuna.Trial) -> float:
    lr = trial.suggest_float("lr", 1e-5, 1e-1, log=True)
    n_layers = trial.suggest_int("n_layers", 1, 5)
    dropout = trial.suggest_float("dropout", 0.0, 0.5)
    hidden = trial.suggest_categorical("hidden", [32, 64, 128, 256])

    model = build_model(lr, n_layers, dropout, hidden)
    val_acc = train_and_eval(model)
    return val_acc

mlflow_callback = MLflowCallback(tracking_uri="http://localhost:5000",
                                  experiment_name="hpo-search")

study = optuna.create_study(direction="maximize",
                            pruner=optuna.pruners.MedianPruner())
study.optimize(objective, n_trials=100, callbacks=[mlflow_callback])

print("best params:", study.best_params)
print("best value:", study.best_value)

# 可视化
fig = optuna.visualization.plot_optimization_history(study)
fig.write_html("optimization_history.html")
```

## 输出格式
- `study.best_params`:最优超参字典。
- `study.best_value`:最优指标值。
- MLflow 中每个 trial 一条 run 记录。
- 可选:参数重要性图、优化历史图(HTML)。

## 约束
- 不手动 grid search,统一走 Optuna。
- 每个 trial 必须记录到 MLflow,丢失视为不合规。
- 使用 pruner 提前终止差 trial,避免浪费算力。
- 超参搜索空间在 objective 中定义,不硬编码在训练逻辑里。
