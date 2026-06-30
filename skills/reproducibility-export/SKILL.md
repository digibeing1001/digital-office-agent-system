# reproducibility-export — 可复现包导出

## 用途
每次实验结束后自动导出可复现包,包含代码版本、依赖环境、配置文件、随机种子、硬件信息,确保他人(或未来的自己)能完整复现实验结果。

## 触发条件
- 一次实验完成并产生结果后。
- 需要交付实验给合作者复现时。
- 准备发表论文需要附可复现材料时。

## 工具依赖
无额外依赖,使用系统自带工具:
```bash
# git、pip/conda 已在环境中
pip install pyyaml  # 用于写 manifest
```

## 操作步骤
1. 记录 git commit hash 和 diff 状态(确认无未提交修改)。
2. 导出依赖:conda 环境用 `conda env export`,pip 用 `pip freeze`。
3. 复制本次 run 使用的配置文件(Hydra 输出的 `.yaml`)。
4. 记录所有随机种子(numpy、torch、random)。
5. 记录硬件信息:GPU 型号、CUDA 版本、CPU、内存。
6. 将以上内容打包到 `reproducibility/<run_id>/` 目录。
7. 生成 `manifest.yaml` 汇总文件。

## 调用示例
```bash
#!/bin/bash
RUN_ID=${1:-$(date +%Y%m%d_%H%M%S)}
OUT_DIR="reproducibility/$RUN_ID"
mkdir -p "$OUT_DIR"

# 1. git 信息
git rev-parse HEAD > "$OUT_DIR/git_commit.txt"
git diff --stat > "$OUT_DIR/git_diff.txt"

# 2. 依赖环境
conda env export > "$OUT_DIR/environment.yml"
pip freeze > "$OUT_DIR/requirements.txt"

# 3. 配置文件
cp -r outputs/*/config.yaml "$OUT_DIR/config.yaml" 2>/dev/null || true

# 4. 硬件信息
nvidia-smi > "$OUT_DIR/gpu_info.txt" 2>/dev/null || true
cat /proc/cpuinfo | grep "model name" | head -1 > "$OUT_DIR/cpu_info.txt"
```

`manifest.yaml` 生成(Python):
```python
import yaml, subprocess, datetime

manifest = {
    "run_id": "20260701_120000",
    "timestamp": datetime.datetime.now().isoformat(),
    "git_commit": subprocess.check_output(["git","rev-parse","HEAD"]).decode().strip(),
    "seeds": {"numpy": 42, "torch": 42, "random": 42},
    "env_file": "environment.yml",
    "config_file": "config.yaml",
    "gpu": "NVIDIA RTX 4090",
    "cuda_version": "12.1",
}
with open("reproducibility/20260701_120000/manifest.yaml", "w") as f:
    yaml.dump(manifest, f, allow_unicode=True)
```

## 输出格式
```
reproducibility/<run_id>/
├── manifest.yaml       # 汇总清单
├── git_commit.txt
├── git_diff.txt
├── environment.yml
├── requirements.txt
├── config.yaml
├── gpu_info.txt
└── cpu_info.txt
```

## 约束
- 五要素缺一不可:git commit、依赖、配置、随机种子、硬件信息。
- 实验结束前若有未提交的 git 修改,必须先提交或显式记录 diff。
- 不接受"依赖见 README"这种模糊描述,必须导出完整环境文件。
