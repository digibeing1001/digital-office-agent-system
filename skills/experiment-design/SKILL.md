# 实验设计技能(Experiment Design)

## 用途
设计在统计与方法学上站得住脚的实验方案,确保评估维度完备、baseline 对比公平、ablation 对应明确假设、样本量足以支撑显著性结论、统计检验方法选择恰当,并产出可复现实验清单与公平性审查报告。

适用于:论文实验章节设计、申报书实验方案、benchmark 评估规划、方法对比研究、消融研究设计等场景。

## 触发条件
满足以下任一条件即激活本技能:
- 用户要求"设计实验""评估方案""消融研究""baseline 对比""算样本量"
- 即将开始论文/申报书的实验章节,需要先有方案
- 需要判断现有实验设计是否公平、是否充分
- 需要选择统计检验方法或做功效分析

## 操作步骤

### 步骤 1:确定评估维度和指标
1. 明确研究问题对应的评估维度(如:准确性、效率、鲁棒性、公平性、可扩展性)
2. 为每个维度定义可计算的量化指标,必须给出数学定义
   - 示例:准确率 = TP/(TP+FP);F1 = 2·P·R/(P+R);延迟 = p50/p95/p99
   - 示例:效率 = 吞吐量(samples/s)或单样本推理时间(ms)
3. 区分主指标(primary,论文核心 claim 依据)与次指标(secondary,辅助说明)
4. 说明指标计算的数据范围(全量 / 子集 / 宏平均 / 微平均)
5. 指标方向性:明确高好还是低好,避免读者误解

### 步骤 2:确定 baseline 和公平对比条件
1. 选 baseline 原则:
   - 经典强 baseline(领域内公认的 SOTA 或标准方法)
   - 近 2-3 年的 SOTA(确保对比有时效性)
   - 简单 baseline(random / majority / linear)作为下界参照
2. **公平性条件清单**(逐项确认):
   - 数据集相同(同一 split / 同一预处理)
   - 超参搜索预算相同(不给自家方法更多调参次数)
   - 计算预算相同(FLOPs / 训练时间 / 参数量可比)
   - 评估协议相同(同一 metrics 实现、同一 random seed 处理)
   - 推理环境相同(硬件 / batch size / 框架版本)
3. 若 baseline 复用原作者报告数字,必须说明并标注"原作者报告值,未在本环境复现"
4. 若某条件无法对齐,标注"非完全公平对比"并解释原因

### 步骤 3:设计 ablation study
1. 列出本方法的每个可剥离组件/模块
2. 为每个组件构造一个对应的科学假设:
   - 形式:"若组件 X 有效,则移除 X 后指标应显著下降"
   - 假设必须可证伪(falsifiable)
3. 每个 ablation 对应一个实验配置(全模型 / 去 X1 / 去 X2 / ...)
4. 避免无假设的"流水线式 ablation"(逐个去掉却没有解释为什么)
5. 优先做关键组件的 ablation,资源不足时合并次要组件

### 步骤 4:选择 benchmark
1. 说明每个 benchmark 覆盖的范围(任务类型 / 数据规模 / 领域 / 难度分布)
2. 优先选用领域内公认的 benchmark(便于他人对比)
3. 如自建数据集,需说明构建流程、标注规范、规模、与公开 benchmark 的关系
4. 避免"只挑对自己有利的 benchmark",要覆盖本方法可能不擅长的场景
5. 记录每个 benchmark 的版本(split / subset / 日期),防止版本漂移

### 步骤 5:计算样本量和统计功效
1. 确定效应量(effect size):
   - Cohen's d / Hedges' g(两组均值对比)
   - 相对提升百分比(领域惯例)
2. 设定显著性水平 α(通常 0.05)和期望功效 power(通常 0.8)
3. 用功效分析公式或工具(statsmodels / G*Power / pingouin)算所需样本量
4. 若实际样本量 < 所需样本量,必须在结果说明中明确"当前样本量不足以支撑显著性结论,结果仅作趋势参考"
5. 多次实验(≥3 次独立运行)取均值±标准差,报告标准差而非标准误(除非说明)

### 步骤 6:确定统计检验方法
按数据特性选择:

| 场景 | 推荐方法 | 备注 |
|------|---------|------|
| 两组均值对比,正态分布 | 配对/独立 t 检验 | 先做正态性检验 |
| 两组对比,非正态 | Wilcoxon 符号秩 / Mann-Whitney U | 非参数 |
| 多组对比 | ANOVA / Kruskal-Wallis | 后接 post-hoc |
| 估计置信区间 | Bootstrap(1000+ 次) | 不依赖分布假设 |
| 多个指标同时检验 | Bonferroni / Holm / FDR 校正 | 控制族错误率 |

1. 说明为什么选这个检验(数据分布 / 样本量 / 配对与否)
2. 报告 p 值 + 效应量 + 置信区间,不只报 p 值
3. 多重比较必须做校正,否则标"未校正,结果应谨慎解读"

### 步骤 7:编写可复现清单
逐项列出,缺一不可:
1. **随机种子**:训练/评估所用 seed(若多个,全列)
2. **软件版本**:框架(Torch/TF 版本)、关键库版本、CUDA 版本
3. **超参数**:学习率 / batch size / 优化器 / epoch / 正则化等,完整列表
4. **硬件环境**:GPU 型号 / 数量 / 内存 / 训练时长
5. **数据细节**:split 划分方式 / 预处理流水线 / 数据增强
6. **代码版本**:commit hash / 仓库链接(若开源)
7. **预训练模型**:版本 / checkpoint 来源(若是基于已有模型)

### 步骤 8:公平性审查
1. 数据公平性:数据集是否存在群体偏差(性别/种族/地域/语言)
2. 评估公平性:是否跨子群体报告指标(demographic parity / equalized odds)
3. baseline 选择公平性:是否遗漏了可能更强的竞品
4. 资源公平性:对比方法的计算预算是否可比
5. 利益冲突声明:是否有商业动机影响 baseline 选择
6. 输出公平性审查清单(pass/warn/fail)

## 输出格式
产出以下文件(建议放在 `outputs/experiment-design/<project>-<date>/`):
- `dimensions-metrics.md`:评估维度和指标定义表(含数学公式)
- `baseline-comparison.md`:baseline 列表 + 公平性条件核对表
- `ablation-plan.md`:ablation 配置 + 对应假设表
- `benchmark-rationale.md`:benchmark 选择理由 + 覆盖范围说明
- `power-analysis.md`:样本量与功效分析过程
- `statistical-tests.md`:统计检验方法选择 + 多重比较校正策略
- `reproducibility-checklist.md`:可复现清单(完整填写)
- `fairness-audit.md`:公平性审查报告
- `experiment-plan.md`:综合实验方案(可执行的总文档)

## 约束
- **baseline 不公平必须标注**:不得掩盖对比条件不对等的事实
- **样本量不足要明说**:严禁用"差异显著"等措辞掩盖功效不足
- **不擅自调指标定义**:指标定义一旦确定,不得为迎合结果事后修改
- **ablation 必须有假设**:无假设的消融不算严谨实验
- **统计检验不乱选**:数据分布不满足时不得强行用参数检验
- **不隐藏不利结果**:某些 benchmark 上本方法不如 baseline 时必须如实报告
- **复现信息要完整**:缺项必须说明原因,不得留空或写"略"
- **不夸大 claim**:实验结果只能支撑特定范围的结论,不得泛化

## 依赖工具/API
- **统计计算**:Python statsmodels / scipy.stats / pingouin(功效分析、检验)
- **Bootstrap**:自实现或使用 resample 库
- **正态性检验**:scipy.stats.shapiro / scipy.stats.normaltest
- **功效分析工具**:G*Power(可选)、statsmodels.stats.power
- **计算量估算**:fvcore / thop(FLOPs 计算)、torchinfo(参数量)
- **数据集加载**:HuggingFace datasets / torchvision / 自建加载器
- **实验跟踪**:Weights & Biases / MLflow / TensorBoard(可选但推荐)

## 关键方法论引用
- Cohen(1988)效应量定义与解读
- Bonferroni / Holm(1979)多重比较校正
- Benjamin-Hochberg(1995)FDR 控制
- Lakens(2014)观测功效与样本量规划教程
- Pineau et al.(2021)ML 可复现性检查清单(ML Reproducibility Checklist)
