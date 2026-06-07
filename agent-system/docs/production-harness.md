# Production Harness For Digital Office Delivery

This document records the production harness direction for the Digital Office multi-Agent system. The goal is production delivery, not prototype-only vibe coding.

## Goal

The harness must raise product, design, engineering, knowledge, memory, and release quality without locking the system to the current Agent names. It should work after migration to a digital law firm, digital accounting firm, digital media studio, or another office package.

The product loop is:

1. Perceive
2. Plan
3. Execute
4. Reflect
5. Iterate

The loop is implemented in `agent-system/ai-native-loop.manifest.json` and exposed through `office-system loop-*` and `office-system iteration-proposal-*` commands.

## Research Snapshot

Observed on 2026-06-07 through GitHub repository metadata.

High-signal coding-agent references:

- [OpenHands](https://github.com/All-Hands-AI/OpenHands), about 76k stars: use an explicit development runtime with actions, observations, and feedback loops.
- [SWE-agent](https://github.com/SWE-agent/SWE-agent), about 19k stars: keep the Agent-computer interface narrow and observable for issue-to-patch work.
- [aider](https://github.com/aider-ai/aider), about 46k stars: repo maps, git-visible diffs, and command/test feedback are central to coding-agent quality.
- [SWE-bench](https://github.com/princeton-nlp/SWE-bench), about 5k stars: coding-agent quality should be judged with reproducible tasks and deterministic tests.

High-signal multi-Agent and durable workflow references:

- [ReAct](https://arxiv.org/abs/2210.03629): interleave reasoning, action, and observation. This maps to Perceive and Execute.
- [Reflexion](https://arxiv.org/abs/2303.11366): use explicit reflection to improve future attempts. This maps to Reflect and Iterate.
- [Generative Agents](https://arxiv.org/abs/2304.03442): separate memory, reflection, and planning. This maps to the separation of project knowledge, company knowledge, KeyMemory relay, and workflow plans.
- [Voyager](https://arxiv.org/abs/2305.16291): build reusable skills through an explicit library. This supports provider-reviewed Agent plugin packages rather than customer-side skill recomposition.
- [MetaGPT](https://arxiv.org/abs/2308.00352): role-based SOP and structured handoff. This supports portable orchestration roles and multi-Agent workflows.
- [AutoGen](https://arxiv.org/abs/2308.08155): multi-Agent conversation needs explicit roles, boundaries, and controllable handoff.
- [LangGraph durable execution](https://docs.langchain.com/oss/python/langgraph/durable-execution): long-running workflows need persisted state, resumability, checkpoints, and human-in-the-loop decisions.
- [RAGAS](https://arxiv.org/abs/2309.15217), [Self-RAG](https://arxiv.org/abs/2310.11511), and [CRAG](https://arxiv.org/abs/2401.15884): retrieval must be measured and critiqued, not blindly trusted.

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

The production harness uses five layers:

1. `agent-system/harness/production-gates.json`: portable gate definitions for product, design, implementation, and workflows.
2. `skills/vibe-design-production-harness`: design-role operating contract and gates.
3. `skills/vibe-coding-production-harness`: implementation-role operating contract and gates.
4. `agent-system/ai-native-loop.manifest.json`: Perceive, Plan, Execute, Reflect, Iterate loop contract.
5. `agent-system/bin/harness-check` and `agent-system/bin/harness-runner`: deterministic local checks that validate registry wiring, loop policy, route stability, and CLI behavior.

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
- keep Agent work inside the resolved workflow steps
- capture observations, artifacts, handoffs, command outputs, and gate results

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
