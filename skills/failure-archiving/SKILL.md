# failure-archiving — 失败实验归档

## 用途
将失败实验(OOM、异常崩溃、结果异常)归档为负样本,保留现场供事后分析,避免重蹈覆辙。失败实验和成功实验同等重要,是方法迭代的重要参考。

## 触发条件
- 训练过程中发生 OOM、CUDA error、NaN loss 等异常时。
- 实验跑完但结果明显异常(指标远低于预期)时。
- 用户提到"实验失败""归档""负样本"时。

## 工具依赖
无额外依赖:
```bash
pip install pyyaml  # 用于写归档元数据
```

## 操作步骤
1. 识别失败类型:OOM / 数值异常(NaN/Inf) / 超时 / 结果偏离预期 / 代码报错。
2. 记录现场:抓取配置文件、完整日志、错误堆栈、最终指标。
3. 创建归档目录 `failure-cases/<date>_<brief_desc>/`。
4. 写入 `failure_meta.yaml`,标注失败原因、现象、可能原因。
5. 不删除任何中间产物(checkpoint、日志、配置)。
6. 汇总到 `failure-cases/index.md` 便于检索。

## 调用示例

归档脚本:
```python
import os, shutil, yaml, datetime, traceback

def archive_failure(run_dir, failure_type, description, traceback_str=None):
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{date_str}_{failure_type}"
    archive_path = os.path.join("failure-cases", archive_name)
    os.makedirs(archive_path, exist_ok=True)

    # 复制现场文件
    for fname in ["config.yaml", "train.log", "metrics.json"]:
        src = os.path.join(run_dir, fname)
        if os.path.exists(src):
            shutil.copy(src, archive_path)

    # 写归档元数据
    meta = {
        "failure_type": failure_type,          # OOM / NaN / timeout / crash / anomaly
        "description": description,
        "timestamp": datetime.datetime.now().isoformat(),
        "traceback": traceback_str,
        "run_dir": run_dir,
        "suspected_cause": "",                  # 事后填写
        "lesson": "",                           # 事后填写
    }
    with open(os.path.join(archive_path, "failure_meta.yaml"), "w") as f:
        yaml.dump(meta, f, allow_unicode=True)

    # 追加到索引
    with open("failure-cases/index.md", "a") as f:
        f.write(f"- [{archive_name}] {failure_type}: {description}\n")

# 捕获异常并归档
try:
    train()
except RuntimeError as e:
    archive_failure("outputs/run_20260701",
                    failure_type="OOM",
                    description=str(e),
                    traceback_str=traceback.format_exc())
```

## 输出格式
```
failure-cases/
├── index.md                          # 失败案例索引
├── 20260701_120000_OOM/
│   ├── failure_meta.yaml             # 失败元数据
│   ├── config.yaml
│   ├── train.log
│   └── metrics.json
└── 20260702_090000_NaN/
    └── ...
```

## 约束
- 不删除失败实验的任何产物,即使是 OOM 也要保留日志。
- 每个 failure_meta.yaml 必须填写 failure_type 和 description,suspected_cause 和 lesson 事后补。
- 失败归档和成功实验一起纳入实验回顾,不可只看成功案例。
