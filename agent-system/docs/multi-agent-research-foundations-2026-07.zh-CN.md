# 多 Agent 数字办公室：研究基础、反例与架构决策

更新日期：2026-07-11

## 执行结论

多 Agent 不是默认模式，也不是产品能力的计数器。它只有在至少满足一项条件时才值得承担通信成本：

1. 任务可拆成互不覆盖的并行工作流；
2. Agent 的工具、模型、证据源或权限真正异构；
3. 下游依赖上游 typed artifact，需要明确交接；
4. maker 与 checker 必须隔离，独立验证能降低风险；
5. 高风险动作必须引入人类或受监管专业判断。

因此 Digital Office 保持 `single_agent` 优先，按需升级为顺序链、并行 DAG、结构化 review/debate 或 human-gated flow。系统衡量的是成功率、证据、成本、延迟、返工和失败类型，不是“参与的 Agent 数量”。

## 论文给出的正面经验

- [MetaGPT（ICLR 2024）](https://proceedings.iclr.cc/paper_files/paper/2024/hash/6507b115562bb0a305f1958ccc87355a-Abstract-Conference.html)：SOP、明确角色产物和可执行反馈能够改善小型软件任务，但角色增加也提高成本。可迁移的是依赖清晰的 PRD/设计/任务/测试 artifact，而不是角色数量。
- [ChatDev（ACL 2024）](https://aclanthology.org/2024.acl-long.810/)：多角色沟通可生成可运行的小型软件，也暴露 token 截断、依赖问题与“已共识但不终止”。每次对话应处理原子任务，完成必须是机器状态，不是自然语言默契。
- [AutoGen（COLM 2024）](https://openreview.net/forum?id=BAakY1hNKS)：writer/executor 与 safeguard/grounding 的能力及信任边界分离能带来收益。只有权限、工具或证据来源真正不同才拆 Agent。
- [AgentVerse](https://arxiv.org/abs/2308.10848)：多 Agent 对部分强模型和多工具任务有效，但弱模型团队可能不如 Solo，正确 Agent 也会被错误同伴说服。应先独立作答，再交换证据并保留异议。
- [Reflexion（NeurIPS 2023）](https://proceedings.neurips.cc/paper_files/paper/2023/hash/1b44b878bb782e6954cd888628510e90-Abstract-Conference.html)：外部反馈驱动的有限反思能改善部分任务；错误 verifier 也会让性能倒退。反思是待验证假设，不能直接写成长期事实。
- [Voyager](https://arxiv.org/abs/2305.16291)：环境反馈、自验证、失败上限和经验证的可执行技能库支持长期学习。数字办公室的 reusable skill 同样需要版本、适用范围、证据和回归测试。

## 论文给出的反例

- [Why Do Multi-Agent LLM Systems Fail?（NeurIPS 2025）](https://proceedings.neurips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html) 把大量失败归入系统设计、Agent 间失配、验证与终止。仅修改角色 prompt 无法修复运行时问题。
- [TheAgentCompany](https://arxiv.org/abs/2412.14161) 的早期 workplace 基线中，最强 Agent 仅自主完成约四分之一任务；长程真实办公工作远未达到“无人值守默认可靠”。产品必须把审批、恢复和证据暴露给用户。
- [AgentBench](https://arxiv.org/abs/2308.03688) 把长期推理、决策和指令遵循列为常见障碍。静态配置检查不能替代轨迹回放和环境验收。
- [More Agents Is All You Need](https://arxiv.org/abs/2402.05120) 的采样投票说明多样本在部分 benchmark 有效，但投票不能验证真实工具副作用、事实来源或权限；它只能作为候选聚合器。
- [On the Resilience of LLM-Based Multi-Agent Collaboration with Faulty Agents](https://arxiv.org/abs/2408.00989) 说明拓扑和错误 Agent 会影响下游韧性。中心节点、顺序链和高连接讨论都需要明确故障隔离。
- [On scalable oversight with weak LLMs judging strong LLMs](https://arxiv.org/abs/2407.04622) 发现 debate 相对直接问答的收益依任务信息结构而变，不能把 debate 当通用质量门。

## 开源框架中值得吸收的运行时语义

- [LangGraph interrupt/checkpoint](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/types.py)：恢复会从节点开头重新执行，因此中断前副作用必须幂等，checkpoint 不能等同于 exactly-once。
- [Microsoft Agent Framework checkpoints](https://learn.microsoft.com/en-us/agent-framework/workflows/checkpoints)：在 superstep 边界保存 executors、待处理消息、请求/响应和共享状态，适合作为跨角色恢复模型。
- [OpenAI Agents SDK HITL](https://openai.github.io/openai-agents-python/human_in_the_loop/)：批准绑定具体 tool call ID，运行状态可序列化恢复，长期 pending task 需要保存代码/Agent 版本。
- [OpenAI Agents SDK tracing](https://github.com/openai/openai-agents-python/blob/main/docs/tracing.md)：trace、span、parent 与自定义事件提供可组合观测结构；敏感输入和输出仍需显式脱敏策略。
- [Restate durable agents](https://docs.restate.dev/ai/patterns/durable-agents)：以 journal 跳过已完成步骤，避免重做 LLM 调用和工具副作用；说明“可恢复”必须覆盖执行结果，而不是只保存聊天历史。
- [Dapr Agents](https://docs.dapr.io/developing-ai/dapr-agents/dapr-agents-core-concepts/)：把 LLM/tool 作为耐久 workflow activity，并提供 pub/sub、状态与 resilience；适合作为未来多节点 adapter，而不是塞进本地 MVP。

## 三分支如何使用这些结论

| 分支 | 必须保留的共享运行时 | 特化验证 |
|---|---|---|
| `main` | ledger、checkpoint、预算、租约、HITL、typed handoff | 产品/设计/代码/法务端到端闭环 |
| `research-team` | 同一运行时，不另造弱化版 loop | provenance、检索记录、方法审批、复现、伦理与引用完整性 |
| `writer-team` | 同一运行时，不以自然语言“交稿”代替状态 | claim-source 对齐、事实核验、作者/编辑隔离、风格与发布审批 |

共享核心改动应从一个提交移植并在三个分支各自跑 production gate；分支只覆盖 registry、profile、workflow pack 和领域 eval，不能复制并悄悄改写核心 `office-system.py`。

## 当前落地

- 单运行单派发租约，避免并发 worker 重复调用同一 Agent；
- 过期租约恢复、损坏租约 fail closed、owner-bound release；
- 租约获取/释放进入哈希链 ledger，`workflow-status` 显示租约状态；
- harness 每个 task/gate 输出进度、耗时和隔离错误，Windows/WSL 输出不再被 UTF-16 破坏；
- checkout 自检显式绑定当前仓库 profiles，不读取用户 `~/.hermes` 产生假结果；
- CI 同时覆盖三个长期分支，并在没有源码 Web UI 的 writer 分支安全跳过 Node build。

## 下一阶段评测协议

用相同模型、工具、token/金额预算和 timeout 比较：

1. Solo；
2. Solo + retry/reflection；
3. 独立采样 + evidence aggregator；
4. 异构多 Agent。

每组报告任务成功率、外部 evidence pass、token/金额、墙钟、人工介入、返工次数和 MAST 失败分布。没有等预算对照，就不能宣称“多 Agent 更好”。
