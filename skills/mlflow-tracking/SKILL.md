# mlflow-tracking — MLflow 实验跟踪

## 用途
每次实验自动记录参数、指标、模型产物和运行日志,保证实验可追溯、可对比、可复现。所有实验结果统一存入 MLflow Tracking Server,通过 UI 横向对比不同 run 的表现。

## 触发条件
- 开始任何一次模型训练、超参搜索或评估实验时。
- 需要对比多次实验结果时。
- 用户提到"记录实验""对比实验""MLflow"时。

## 工具依赖
```bash
pip install mlflow
# 启动 tracking server(可选,本地也可用 file store)
mlflow ui --host 0.0.0.0 --port 5000
```

## 操作步骤
1. 启动 MLflow tracking server,或使用本地 file store(`mlflow:///` 目录)。
2. 在实验代码中设置 `mlflow.set_tracking_uri()` 和 `mlflow.set_experiment()`。
3. 用 `with mlflow.start_run():` 包裹训练逻辑。
4. 在 run 内调用 `mlflow.log_params()` 记录超参,`mlflow.log_metrics()` 记录指标,`mlflow.log_artifacts()` 记录模型/图。
5. 记录 git commit hash 以便追溯代码版本。
6. 训练结束后打开 MLflow UI,对比不同 run 的指标曲线。

## 调用示例
```python
import mlflow
import subprocess

# 获取当前 git commit
git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("my-experiment")

with mlflow.start_run():
    # 记录代码版本
    mlflow.set_tag("git_commit", git_commit)

    params = {"lr": 1e-3, "batch_size": 64, "epochs": 100}
    mlflow.log_params(params)

    for epoch in range(params["epochs"]):
        loss, acc = train_one_epoch(epoch)
        mlflow.log_metric("loss", loss, step=epoch)
        mlflow.log_metric("acc", acc, step=epoch)

    # 保存模型和配置
    mlflow.log_artifact("config.yaml")
    mlflow.pytorch.log_model(model, "model")
```

对比多个 run:
```bash
# 启动 UI 后浏览器访问
# http://localhost:5000 → 选 experiment → 勾选多个 run 对比
```

## 输出格式
- MLflow Server 中的 run 记录,包含:参数、指标(支持时序)、模型产物、git commit tag。
- 可通过 `mlflow.search_runs()` 导出对比表为 pandas DataFrame。

## 约束
- 不靠手动记日志文件,所有记录必须走 MLflow API。
- 每次 run 必须记录 git commit hash,缺失视为不合规。
- 指标必须按 step 记录时序值,不可只记最终值。
