# Digital Office 耐久运行时契约

本契约定义 Digital Office 在长期 loop 与多进程宿主中的最低运行时语义。它约束的是代码执行层，不依赖 Agent 在提示词中“自觉遵守”。

## 单运行单派发

同一个 `run_id` 在任意时刻只允许一个工作进程执行 `workflow-dispatch-next`。运行时在 `agent-system/runs/<run_id>/dispatch-lease.json` 保存租约，并用独立文件锁完成租约的原子获取与释放。

- 活跃租约存在时，第二个进程必须快速返回 `dispatch_already_leased`，不得重复调用 Agent 或工具。
- 租约绑定唯一 `lease_id`；只有持有该 ID 的进程可以释放，避免旧进程误删新租约。
- 租约包含 `owner`、`acquired_at`、`expires_at`、`ttl_seconds` 与最终 `outcome`，供状态页和审计复查。
- `workflow-status --run-id <id>` 返回 `dispatch_lease` 快照，操作者可以区分正在执行、已释放、已过期和状态损坏。
- 获取和释放事件写入哈希链 run ledger，使重复派发调查可以从事件证据恢复，而不是依赖模型解释。

## 过期恢复

外部 Agent 调用可能因进程崩溃、宿主重启或网络中断而没有机会执行 `finally`。因此租约必须有明确过期时间：

1. 正常路径在 Agent 调用结束后释放租约并记录 outcome。
2. 新工作进程只能替换已经过期的租约。
3. 无法解析或缺少有效过期时间的租约一律 fail closed；操作者先修复或隔离损坏状态，系统不得猜测后继续派发。

当前租约 TTL 至少覆盖 Agent 执行 timeout 并额外保留恢复余量。未来若支持超长活动，应增加心跳续租，而不是简单放大为无限租约。

## 幂等与副作用边界

派发租约解决“两个工作进程同时选择同一个 queued task”的竞争，但不替代工具级幂等。所有会产生外部副作用的工具仍应：

- 接收稳定的 `idempotency_key`，建议由 `run_id + task_id + tool_call_id` 派生；
- 在副作用发生前写入意图或使用目标系统的幂等接口；
- 把可重试错误与永久错误分开；
- 在人工中断前完成检查点，恢复后不得盲目重放已完成副作用。

这与 run ledger、checkpoint、预算/终止条件共同构成耐久 loop；任何单一机制都不能独立提供 exactly-once 业务语义。

## 验证

```bash
python3 agent-system/tests/runtime-contract-smoke.py
agent-system/bin/harness-runner --task durable-dispatch-production --no-write
```

测试覆盖活跃租约阻断、所有权校验、正常释放、崩溃后的过期恢复，以及损坏租约的 fail-closed 行为。
