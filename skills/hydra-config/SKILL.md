# hydra-config — Hydra 配置管理

## 用途
实验配置的统一管理和扫参(sweep)。所有超参、数据路径、模型结构通过 YAML 配置文件管理,支持命令行覆盖和多组配置组合运行,杜绝硬编码。

## 触发条件
- 实验需要管理多套配置(不同数据集/模型/超参)时。
- 需要做配置扫参(如 lr × batch_size 的笛卡尔积)时。
- 用户提到"配置管理""Hydra""sweep"时。

## 工具依赖
```bash
pip install hydra-core
```

## 操作步骤
1. 在项目 `conf/` 目录下编写 `config.yaml` 主配置文件。
2. 用 `@hydra.main(version_base=None, config_path="conf", config_name="config")` 装饰主函数。
3. 命令行覆盖:`python train.py lr=0.01 model.hidden=128`。
4. 多组扫参:`python train.py --multirun lr=0.01,0.001 batch_size=32,64`。
5. 配置变更通过 git 追踪,每次 run 的配置自动由 Hydra 输出到 `outputs/`。

## 调用示例
`conf/config.yaml`:
```yaml
defaults:
  - model: mlp
  - data: imagenet

lr: 0.001
batch_size: 64
epochs: 100
seed: 42
```

`conf/model/mlp.yaml`:
```yaml
name: mlp
hidden: 128
layers: 3
dropout: 0.1
```

训练代码:
```python
import hydra
from omegaconf import DictConfig
import mlflow

@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg: DictConfig):
    print(f"训练配置: {cfg}")
    model = build_model(cfg.model)
    train_loader = load_data(cfg.data, cfg.batch_size)

    with mlflow.start_run():
        mlflow.log_params(dict(cfg))
        for epoch in range(cfg.epochs):
            loss = train_one_epoch(model, train_loader, cfg.lr)
            mlflow.log_metric("loss", loss, step=epoch)

if __name__ == "__main__":
    main()
```

扫参:
```bash
# 多组配置组合运行
python train.py --multirun lr=0.01,0.001,0.0001 batch_size=32,64,128
```

## 输出格式
- Hydra 自动在 `outputs/<date>/<time>/` 下保存本次 run 的完整配置 `.yaml`。
- 扫参结果汇总在 `multirun.yaml`。

## 约束
- 所有超参必须通过 Hydra 配置,不硬编码在 Python 代码中。
- 配置文件纳入 git 版本管理。
- 命令行覆盖的参数也会被 Hydra 记录到输出配置,保证可复现。
