# AutoGen → microsoft/agent-framework 迁移路径

> 状态：规划中 | 创建：2026-07-01 | 关联：loop-engineering.zh-CN.md

## 背景

当前项目的 `ai-native-loop.manifest.json` 研究基础引用了 AutoGen 的异步人工反馈机制。微软已将 AutoGen 与 Semantic Kernel 两团队合并，发布 `microsoft/agent-framework` 作为继任者：

- `microsoft/autogen`（旧仓库）已于 2026-04 进入维护模式，停止主要更新。
- `microsoft/agent-framework`（新仓库，约 12K star）是官方推荐迁移目标，提供原生 checkpoint/resume、workflow 编排、GroupChat 等。

## 迁移收益

| 能力 | 旧 AutoGen | agent-framework |
|---|---|---|
| Checkpoint/Resume | 需自行实现 | 原生三种模式：`CheckpointAndResume`、`CheckpointAndRehydrate`、`CheckpointWithHumanInput` |
| 跨进程恢复 | 不支持 | `CheckpointAndRehydrate` 支持新实例注水恢复（crash 后冷启动） |
| Workflow 编排 | GroupChat | Workflow + GroupChat + Actor 模型 |
| HarnessAgent | 无 | 2026-05 新增，带可用特性集与样例 |
| 维护状态 | 维护模式 | 活跃（2026-07 仍在推送） |

## 迁移策略

### 阶段一：并行（低风险）
- 保留现有 AutoGen 引用作为研究基础记录。
- 新增 `microsoft/agent-framework` 作为 checkpoint/resume 的参考实现。
- 在 `ai-native-loop.manifest.json` 的 `research_foundations` 中新增 agent-framework 条目。

### 阶段二：试点（中风险）
- 在单一工作流（建议 `parallel_expert_dag`）中试点 agent-framework 的 `CheckpointAndRehydrate` 模式。
- 对比试点前后的 run ledger 一致性与恢复成功率。
- 保持与现有 controller 决策的兼容（continue/replan/retry/wait_human/complete/fail）。

### 阶段三：全量切换（需评审）
- 评估试点结果，决定是否全量切换。
- 全量切换需更新 `research_foundations` 中 AutoGen 条目的状态标记。
- 通过 `harness/tasks/agent-lifecycle-production.json` 评估验证。

## 关键注意事项

1. **不破坏现有 controller**：agent-framework 的 workflow 是节点内部执行器，不替换四节点 controller。controller 仍拥有状态转移权。
2. **Checkpoint 三模式的映射**：
   - `CheckpointAndResume` → 同实例暂停/恢复（对应现有 `paused` 状态）
   - `CheckpointAndRehydrate` → 跨实例恢复（对应 crash 后冷启动，当前缺失）
   - `CheckpointWithHumanInput` → 人工审批断点（对应现有 `waiting_human_judgment`）
3. **Human feedback 兼容**：现有 `wait_human` controller 决策与 `CheckpointWithHumanInput` 语义一致，迁移后行为不变。
4. **嵌套 loop**：agent-framework 的 checkpoint 是否支持嵌套 loop 需在试点阶段验证（参考 inspect_ai 的 reentrant checkpointer 设计）。

## 参考仓库

- 迁移目标：https://github.com/microsoft/agent-framework
- 旧仓库（维护模式）：https://github.com/microsoft/autogen
- 嵌套 loop checkpoint 参考：https://github.com/UKGovernmentBEIS/inspect_ai

## 当前状态

本次更新已在 `ai-native-loop.manifest.json` 的 `research_foundations` 新增 Anthropic Multi-Agent Research System 条目。agent-framework 的正式条目将在阶段二试点启动时新增，以避免在未验证前就将其列为已采用基础。
