# version-management — 版本管理

## 用途
对实验代码和数据做版本管理,确保每次实验都有对应的代码快照和变更记录,实验结果可追溯到具体的代码版本,支持里程碑标记和依赖固化。

适用于:实验代码 git 管理、实验数据版本记录、里程碑打 tag、复现包依赖导出等场景。

## 触发条件
- 用户要求"管版本""git commit""打 tag""导出依赖"时。
- 每次实验开始前/结束后需要固化代码版本时。
- 用户提到"版本管理""记录变更""复现包"时。

## 操作步骤
1. **实验前 commit**:每次实验开始前,把当前代码 git commit,记录 commit hash 作为本次实验的代码基线。
2. **实验后记录变更**:实验结束后,把实验中改动的代码、配置、超参记录到变更说明,关联实验结果。
3. **打 tag 标里程碑**:对重要里程碑(如达到 SOTA、投稿版本、可复现版本)打 git tag,附说明。
4. **导出依赖清单**:导出当前环境的依赖清单(pip freeze / conda env export / requirements.txt),与代码版本一起归档。
5. **数据版本同步**:实验所用数据的版本(数据集 hash / split 版本 / 预处理脚本版本)一并记录。

## 调用示例
```bash
# 实验前固化代码版本
git add -A && git commit -m "exp: baseline run before ablation"
COMMIT_HASH=$(git rev-parse HEAD)
echo "本次实验代码版本: $COMMIT_HASH" > outputs/exp_record.txt

# 打里程碑 tag
git tag -a v1.0-sota -m "达到 SOTA 的投稿版本"

# 导出依赖清单
pip freeze > requirements_frozen.txt
```

## 输出格式
- 版本记录文件,包含:
  - git commit hash
  - 变更说明(本次改了什么、为什么)
  - 依赖清单(requirements_frozen.txt)
  - 数据版本(数据集 hash / split 版本)
- git tag(里程碑标记)。

## 约束
- **每次实验必须有 git commit**:不得在未提交代码的情况下跑实验。
- 依赖清单必须与实验环境一致,不得手工编辑。
- 数据版本必须一并记录,代码版本单独不够。
- tag 只用于真实里程碑,不滥用。
