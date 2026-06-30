# reproducibility-packaging — 可复现包封装

## 用途
实验结束后导出可复现包,把代码、数据引用、配置、随机种子、硬件信息、运行命令打包归档,使第三方研究者仅凭此包即可复现实验结果。

适用于:论文投稿附可复现包、开源发布、实验归档、复现验证等场景。

## 触发条件
- 用户要求"导出可复现包""打包实验""归档复现"时。
- 论文投稿需要附 reproducibility package 时。
- 用户提到"复现包""reproducibility""打包"时。

## 操作步骤
1. **收集 git commit**:记录当前代码的 commit hash,确保代码版本可追溯。
2. **收集依赖清单**:导出 requirements.txt / conda env / 环境镜像,固化软件版本。
3. **收集配置文件**:把实验所用 config 文件(yaml / json)打包,含超参和数据路径。
4. **收集随机种子**:记录所有随机种子(训练 / 评估 / 数据 shuffle),不止一个就全列。
5. **收集硬件信息**:记录 GPU 型号 / 数量 / 内存 / 训练时长 / 推理环境。
6. **收集运行命令**:把跑通实验的完整命令行记录下来,含参数和顺序。
7. **打包**:把以上所有内容组织到统一目录,附 README 说明如何运行。

## 调用示例
```bash
# 打包目录结构
reproducibility_package/
├── code/                 # 代码(git archive 或子模块)
├── configs/              # 配置文件
├── requirements.txt      # 依赖清单
├── seeds.txt             # 随机种子列表
├── hardware_info.txt     # 硬件信息
├── run_commands.sh       # 运行命令
└── README.md             # 运行说明

# 生成 git 快照
git archive --format=tar HEAD -o reproducibility_package/code/code.tar
```

## 输出格式
可复现包目录,含:
- 代码快照(commit hash)
- 依赖清单(软件版本)
- 配置文件(超参 / 数据路径)
- 随机种子列表
- 硬件信息(GPU / 内存 / 时长)
- 运行命令(完整命令行)
- README(如何复现)

## 约束
- **缺一不可**:以上七项必须齐全,缺项必须说明原因,不得留空或写"略"。
- 数据若涉密不能打包,必须给出数据申请方式和引用说明。
- 运行命令必须可复制粘贴直接执行,不得有"请自行修改"的模糊步骤。
- 包必须经一次干净环境复现验证,确认能跑通。
