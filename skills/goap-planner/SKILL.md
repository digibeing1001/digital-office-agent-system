# goap-planner — GOAP A* 目标规划

## 用途
基于 GOAP（Goal-Oriented Action Planning）A* 算法，将自然语言目标分解为可执行的动作序列。在状态空间中搜索从当前状态到目标状态的最短可行路径，动作失败时从当前状态重规划而非重启。是 Loop 工程 Decide 节点的规划能力增强，实现"定义终态 → AI 自动规划路径 → 失败重规划"。

适用于:复杂多步骤任务的路径规划、课题立项后的实验计划分解、跨角色任务编排、失败后的动态重规划。

## 触发条件
- Decide 节点需要将目标分解为动作序列
- 课题规划师需要生成分阶段的实验计划
- 协调策略需要编排多角色协作流程
- Act 节点动作失败后的重规划
- 用户要求"规划""分解任务""制定计划"

## 操作步骤

### 步骤 1:定义状态空间
```python
from dataclasses import dataclass, field
from typing import Set

@dataclass
class WorldState:
    """世界状态：用一组布尔/数值谓词表示"""
    predicates: dict = field(default_factory=dict)
    
    def satisfies(self, goal_state: "WorldState") -> bool:
        """检查当前状态是否满足目标状态"""
        for key, value in goal_state.predicates.items():
            if self.predicates.get(key) != value:
                return False
        return True
    
    def apply_effects(self, effects: dict) -> "WorldState":
        """应用动作效果，返回新状态"""
        new_preds = self.predicates.copy()
        new_preds.update(effects)
        return WorldState(predicates=new_preds)
    
    def heuristic_distance(self, goal: "WorldState") -> float:
        """A* 启发式：未满足的谓词数量"""
        dist = 0
        for key, value in goal.predicates.items():
            if self.predicates.get(key) != value:
                dist += 1
        return dist
```

### 步骤 2:定义动作
```python
@dataclass
class GOAPAction:
    """GOAP 动作：前置条件 + 效果 + 成本"""
    name: str
    preconditions: dict          # 前置条件谓词
    effects: dict                # 执行后效果谓词
    cost: float = 1.0            # 动作成本
    assigned_agent: str = None   # 分配的角色
    
    def is_executable(self, state: WorldState) -> bool:
        """检查在当前状态下是否可执行"""
        for key, value in self.preconditions.items():
            if state.predicates.get(key) != value:
                return False
        return True
    
    def execute(self, state: WorldState) -> WorldState:
        """执行动作，返回新状态"""
        return state.apply_effects(self.effects)
```

### 步骤 3:LLM 生成动作库
```python
def generate_action_library(goal: str, context: dict) -> list:
    """LLM 根据目标生成候选动作库"""
    prompt = f"""
    目标: {goal}
    上下文: {context}
    
    生成实现该目标所需的动作清单。每个动作包含:
    - name: 动作名
    - preconditions: 前置条件（状态谓词）
    - effects: 执行后效果（状态谓词）
    - cost: 成本估计（1-10）
    - assigned_agent: 分配角色
    
    输出 JSON 数组。
    """
    actions_json = llm_call(prompt)
    return [GOAPAction(**a) for a in json.loads(actions_json)]
```

### 步骤 4:A* 搜索
```python
import heapq

def goap_a_star(initial: WorldState, goal: WorldState, actions: list) -> list:
    """A* 搜索最短可行路径"""
    # 优先队列: (f_score, counter, state, path)
    counter = 0
    open_set = [(initial.heuristic_distance(goal), counter, initial, [])]
    visited = set()
    
    while open_set:
        f, _, current, path = heapq.heappop(open_set)
        
        # 目标达成
        if current.satisfies(goal):
            return path
        
        # 状态去重
        state_key = frozenset(current.predicates.items())
        if state_key in visited:
            continue
        visited.add(state_key)
        
        # 扩展可执行动作
        for action in actions:
            if action.is_executable(current):
                new_state = action.execute(current)
                new_path = path + [action]
                g = len(new_path)  # 实际成本
                h = new_state.heuristic_distance(goal)
                f = g + h
                counter += 1
                heapq.heappush(open_set, (f, counter, new_state, new_path))
    
    return None  # 无可行路径
```

### 步骤 5:失败重规划
```python
def replan_on_failure(current_state: WorldState, goal: WorldState, 
                      actions: list, failed_action: GOAPAction) -> list:
    """动作失败后从当前状态重规划（非重启）"""
    # 标记失败动作为高成本（避免重复选择）
    for a in actions:
        if a.name == failed_action.name:
            a.cost = 999  # 惩罚失败动作
    
    # 从当前状态重新搜索
    new_path = goap_a_star(current_state, goal, actions)
    
    if new_path is None:
        # 无可行路径 → 升级 human_gate
        return None
    return new_path
```

### 步骤 6:生成可执行计划
```python
def generate_executable_plan(path: list) -> dict:
    """将 GOAP 路径转为可执行计划"""
    return {
        "total_steps": len(path),
        "total_cost": sum(a.cost for a in path),
        "steps": [
            {
                "step": i + 1,
                "action": a.name,
                "agent": a.assigned_agent,
                "preconditions": a.preconditions,
                "expected_effects": a.effects,
                "cost": a.cost,
            }
            for i, a in enumerate(path)
        ],
        "failure_recovery": "动作失败时从当前状态重规划，不重启",
    }
```

## 输出格式
```json
{
  "total_steps": 5,
  "total_cost": 12,
  "steps": [
    {"step": 1, "action": "literature_search", "agent": "literature-researcher", "cost": 2},
    {"step": 2, "action": "gap_analysis", "agent": "pi", "cost": 3},
    {"step": 3, "action": "experiment_design", "agent": "methodologist", "cost": 3},
    {"step": 4, "action": "run_experiment", "agent": "research-engineer", "cost": 2},
    {"step": 5, "action": "write_paper", "agent": "academic-writer", "cost": 2}
  ],
  "failure_recovery": "动作失败时从当前状态重规划，不重启"
}
```

## 约束
- 动作库由 LLM 生成后必须人工或质检员 review（防止幻觉动作）
- A* 搜索最大节点数 1000（防止搜索爆炸）
- 重规划最多 3 次（与 cost-control max_rework_cycles 对齐）
- 无可行路径时必须升级 human_gate，不得强行执行
- 动作成本纳入 cost-control 预算计算
- 每次规划记录到 observability trace 的 decide node_span

## 与现有 skill 的关系
- **与 ai-native-loop.manifest.json 协同**:goap-planner 是 Decide 节点的规划引擎
- **与 milestone-tracking 协同**:goap-planner 生成步骤后，milestone-tracking 跟踪进度
- **与 cost-control.policy.json 协同**:动作成本纳入预算
- **与 cross-run-memory 协同**:成功路径存入记忆库供复用

## 依赖工具/API
- LLM API（动作库生成）
- 无外部依赖（纯算法实现）

## 关键方法论引用
- GOAP (Goal-Oriented Action Planning): Orkin, 2003 (AI Game Programming Wisdom)
- Ruflo GOAP A* 规划器: https://github.com/ruvnet/ruflo
- A* 算法: Hart, Nilsson & Raphael, 1968
