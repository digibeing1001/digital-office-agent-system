# Production Harness For Digital Office Delivery

This document records the production harness direction for the Digital Office multi-Agent system. The goal is production delivery, not prototype-only vibe coding.

## Goal

The harness must raise product, design, engineering, knowledge, memory, and release quality without locking the system to the current Agent names. It should work after migration to a digital law firm, digital accounting firm, digital media studio, or another office package.

The task runtime uses four composable work nodes:

1. Context
2. Decide
3. Act
4. Evaluate

A deterministic controller chooses Continue, Replan, Retry, Wait Human, Complete, Fail, Cancel, or Budget Exhausted. Task rework stays inside bounded cycles and budgets. System changes still use separately confirmed `iteration-proposal-*` commands.

## Design Patterns

High-signal multi-Agent and durable workflow patterns:

- Reasoning-action interleaving: interleave reasoning, action, and observation. This informs Decide and Act inside a bounded controller.
- Evaluation-driven retry: use explicit evaluation feedback to improve a later attempt. This informs Evaluate and controller Replan or Retry decisions.
- Memory-reflection-planning separation: separate memory, reflection, and planning. This maps to the separation of project knowledge, company knowledge, KeyMemory relay, and workflow plans.
- Reusable skill library: build reusable skills through an explicit library. This supports provider-reviewed Agent plugin packages rather than customer-side skill recomposition.
- Role-based SOP: role-based SOP and structured handoff. This supports portable orchestration roles and multi-Agent workflows.
- Multi-agent conversation roles: multi-Agent conversation needs explicit roles, boundaries, and controllable handoff.
- [LangGraph durable execution](https://docs.langchain.com/oss/python/langgraph/durable-execution): long-running workflows need persisted state, resumability, checkpoints, and human-in-the-loop decisions.
- Retrieval quality measurement: retrieval must be measured and critiqued, not blindly trusted.

High-signal skill and workflow sources:

- [ECC](https://github.com/affaan-m/ECC), about 210k stars: harness construction and regression testing patterns.
- [awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills), about 64k stars: curated skill discovery source.
- [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills), about 40k stars: large installable agentic skill library.
- [awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules), about 40k stars: AI editor rules and framework-specific coding conventions.
- [claude-task-master](https://github.com/eyaltoledano/claude-task-master), about 27k stars: task decomposition and implementation status discipline.
- [12-factor-agents](https://github.com/humanlayer/12-factor-agents), about 23k stars: durable LLM application control principles.
- [ai-dev-tasks](https://github.com/snarktank/ai-dev-tasks), about 8k stars: task lifecycle and AI dev-agent status management.

These sources are not installed directly into production. They are candidate sources and design references. Enterprise deployments must stage, review, adapt, verify, and approve before any external skill becomes active.

## Harness Model

The production harness uses eight layers:

1. `agent-system/harness/production-gates.json`: portable gate definitions for product, design, implementation, and workflows.
2. `skills/vibe-design-production-harness`: design-role operating contract and gates.
3. `skills/vibe-coding-production-harness`: implementation-role operating contract and gates.
4. `agent-system/ai-native-loop.manifest.json`: Context, Decide, Act, Evaluate work nodes, deterministic transitions, budgets, progress policy, and terminal states.
5. `agent-system/coordination.policy.json`: topology selection for single-Agent, secretary-led, sequential specialist, parallel DAG, and human-gated workflows.
6. `agent-system/runs/<run_id>/ledger.jsonl`: hash-chained execution trace for replay, audit, and drift diagnosis.
7. `agent-system/evals/*.json`: deterministic eval suites for judgment gates, coordination policy, multilingual regressions, and rule-scope inference.
8. `agent-system/bin/harness-check` and `agent-system/bin/harness-runner`: deterministic local checks that validate registry wiring, loop policy, route stability, replayability, and CLI behavior.

The required task set includes `workflow-control-plane-production`, which verifies the GUI-facing workflow run, task inbox, approval center, authorization decision, audit event, notification, confirmation-to-resume signal, and secretary clarification loop. It also includes `runtime-replay-production` and `multilingual-agent-eval-production`, which verify checkpointed replay, typed handoff envelopes, coordination policy decisions, and multilingual judgment regressions.

## Runtime Replay Contract

Production work must not depend on an Agent's private conversational memory. A run is production-replayable only when these records exist:

- `run.json`: durable workflow state, current stage, linked tasks, blockers, judgments, checkpoints, and handoffs.
- `ledger.jsonl`: append-only, hash-chained runtime events with input/output hashes, artifact refs, model/provider metadata when available, and links to checkpoint or handoff ids.
- `checkpoints/<checkpoint_id>.json`: resumable state snapshots with `state_hash`, `resume_cursor`, artifacts, and optional human judgment case.
- `handoffs/<handoff_id>.json`: typed cross-Agent envelopes with stable context/task identity, facts and provenance, omissions, artifact references, context budget, context hash, and recipient acknowledgment.
- eval report: deterministic release-critical checks from `office-system eval-run`.

If any of these are missing for a production claim, the run is still a draft or debug run, not a completed production workflow.

## Coordination Contract

The secretary must choose a coordination mode from `coordination.policy.json` instead of deciding implicitly from prompt style or the number of available Agents. The default modes are:

- `single_agent`: one specialist can own the task end to end.
- `secretary_centralized`: routing or scope is ambiguous.
- `sequential_specialist_chain`: ordered specialist handoffs are required.
- `parallel_expert_dag`: independent workstreams can run in parallel and merge later.
- `human_gated`: risk is high, regulated, externally visible, or irreversible.

Every cross-Agent handoff needs `handoff-create`; every pause/resume boundary needs `checkpoint-create`; every production release needs the multilingual eval suite to pass.

Every approval or human-judgment confirmation must produce a structured
`resume_signal`. If that signal says `control_decision=continue` and
`requires_dispatch=true`, the next backend action is
`workflow-dispatch-next --confirmed`; the Agent should not respond with another
pre-execution plan and stop.

## Production Loop Contract

Perceive:

- gather current user request, tenant/user/project identity, permissions, project knowledge, company knowledge, licensed reference mounts, KeyMemory relay, route candidates, and system health
- never let KeyMemory override source-backed project or company knowledge
- log licensed industry reference access

Plan:

- select portable roles before concrete Agent ids
- define workflow, handoff contract, acceptance criteria, risk, test plan, and rollback
- ask for user confirmation when plan risk is high

Execute:

- dispatch through `scripts/agent-router`
- select the installed host adapter or direct model API adapter explicitly
- fail closed when an API provider, model, or credential is missing; never silently simulate a successful call
- keep Agent work inside the resolved workflow steps
- capture observations, artifacts, handoffs, command outputs, and gate results

Direct model API calls are tested against a local fake provider in
`agent-system/tests/model-gateway-smoke.py`. The test covers all supported wire
protocols, retryable rate limits, secret redaction, private runtime settings,
and the complete router-to-gateway path without spending tokens or requiring an
external account.

Reflect:

- compare outcome to the plan, evidence, gates, user goal, and known risks
- produce findings and methodology drafts without hiding failed gates
- create iteration proposals when a system improvement is warranted

Iterate:

- never apply a change silently
- create an explicit iteration proposal with change summary, expected impact, risk, rollback, affected objects, and regression checks
- wait for user decision: Confirm, Tune Through Conversation, Pause, Reject
- apply only after Confirm and record the regression result

## Product Design Quality Gates

The `product` role must produce:

- user and job-to-be-done
- goal, non-goals, and constraints
- acceptance criteria
- dependencies and risks
- handoff to design or implementation

The design role should not start if product intent is still ambiguous.

## Vibe Design Quality Gates

The `design` role must produce:

- interaction flow
- state list
- responsive behavior
- visual direction
- accessibility notes
- implementation handoff

For skeuomorphic digital office work, visual metaphors must map to actual product objects or actions. Decoration alone is not enough.

## Vibe Coding Quality Gates

The `implementation` role must produce:

- code diff
- deterministic command/test output
- smoke result
- risk notes
- rollback notes

LLM review can help, but it is secondary. A production claim requires deterministic gates to pass.

## GUI Contract

The GUI should show:

- current workflow
- current AI native loop stage
- current role and resolved Agent
- gate status
- artifacts generated by each role
- failed gate reason and next action
- iteration proposals and their decision status

If a required gate fails, the task returns to secretary for clarification or rework.

The GUI must not expose self-iteration as a hidden background process. Iteration proposals are user-visible work items.

## Migration Rule

Do not hard-code `pm`, `vibe-designer`, or `coder` in GUI product behavior. Use orchestration roles:

- `product`
- `design`
- `implementation`

Agent names are deployment-specific mappings.
