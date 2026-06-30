# causal-inference — 因果推断

## 用途
区分相关性和因果性。使用 DoWhy + EconML 进行因果图建模、效应估计和反驳检验,确保因果性 claim 有据可依,而非仅凭观测相关性下结论。

## 触发条件
- 需要声称"A 导致 B"这类因果性结论时。
- 观察到相关性但不确定是否存在混杂因素时。
- 用户提到"因果""causal""混杂变量""DoWhy"时。

## 工具依赖
```bash
pip install dowhy econml
```

## 操作步骤
1. 建因果图:明确处理(treatment)、结果(outcome)、混杂(confounder)变量。
2. 识别估计量:用 DoWhy 自动识别可用的估计策略(后门准则等)。
3. 估计效应:用 EconML 的双重机器学习 / 工具变量法估计因果效应。
4. 反驳检验:用安慰剂数据、随机共同原因等反驳方法检验稳健性。
5. 若 claim 因果:必须列出已知混杂变量并做敏感性分析。

## 调用示例
```python
import dowhy
from dowhy import CausalModel
import pandas as pd

# 示例:估计"训练数据量(treatment)对模型精度(outcome)的因果效应"
df = pd.read_csv("experiment_data.csv")

model = CausalModel(
    data=df,
    treatment=["data_size"],
    outcome=["accuracy"],
    graph="""
        digraph {
            data_size -> accuracy;
            model_capacity -> data_size;
            model_capacity -> accuracy;
            task_difficulty -> accuracy;
            hardware -> data_size;
        }
    """
)

# Step 1-2: 识别
identified_estimand = model.identify_effect()
print("估计量:", identified_estimand)

# Step 3: 估计(双重机器学习)
estimate = model.estimate_effect(
    identified_estimand,
    method_name="backdoor.econml.dml.DML",
    method_params={
        "init_params": {"model_final": "sklearn.ensemble.GradientBoostingRegressor",
                        "model_t": "sklearn.ensemble.GradientBoostingRegressor"},
        "fit_params": {}
    }
)
print(f"因果效应估计: {estimate.value}")

# Step 4: 反驳检验
refutations = [
    model.refute_estimate(identified_estimand, estimate, "placebo_treatment_refuter"),
    model.refute_estimate(identified_estimand, estimate, "random_common_cause"),
    model.refute_estimate(identified_estimand, estimate, "data_subset_refuter"),
]
for r in refutations:
    print(f"{r.refutation_type}: 效应={r.new_effect:.4f}")

# Step 5: 敏感性分析(未测混杂的影响)
# 若反驳后效应方向不变,则 claim 较稳健
```

## 输出格式
- 因果效应估计值(ATE / CATE)。
- 反驳检验报告:各反驳方法下的新效应值。
- 因果图(DAG)可视化。

## 约束
- 严格区分"相关性 claim"和"因果性 claim",措辞不可混淆。
- 因果性 claim 必须列出已知混杂变量,并说明哪些混杂未被测量。
- 反驳检验未通过时,不得声称因果效应成立。
- 观测数据只能 claim 条件因果(给定已测混杂),不可 claim 总体因果。
