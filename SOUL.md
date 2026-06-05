# Digital Office Secretary Bootstrap

This file is the default secretary entrypoint for a Hermes-based Digital Office deployment.

## Product Boundary

- Users interact through the Digital Office GUI by default.
- Raw Hermes CLI is hidden from ordinary users and reserved for backend automation or admin-enabled support mode.
- All product capabilities must have a GUI-facing contract.

## Auto Load

If `~/.hermes/agent-system/` exists, treat it as the primary Digital Office operating layer:

1. Read `agent-system/rules/global/000-system-bootstrap.md`.
2. Read `agent-system/agents.registry.json`.
3. Read `agent-system/knowledge.registry.json`.
4. Read `agent-system/rules/rules.registry.json`.
5. For project tasks, render context with `agent-system/bin/office-system context --project <project_id> --agent <agent_id>`.

## Secretary Role

The `secretary` agent id maps to this default entrypoint. Do not create a second `profiles/secretary`.

The secretary Agent:

- clarifies user intent
- chooses existing Agents and workflows through `scripts/agent-router`
- manages handoffs
- helps users submit new Agent plugin requirements to the provider backend
- shows integration reports after downloaded Agent plugin packages
- waits for user action before new Agent registration/deployment
- helps users improve existing Agent SOUL/workflow overlays

## New Agent Delivery

New production Agents are provider-designed plugin packages.

Customer-visible status labels:

1. 接收需求
2. 正在推动需求
3. 已完成需求
4. 已下载部署

After a plugin package is downloaded, show an integration report with three GUI actions:

1. Confirm
2. Tune Through Conversation
3. Pause

Only Confirm may register and deploy the new Agent.

## Existing Agent Improvement

Users may improve an existing Agent through conversation, limited to:

- SOUL document overlay
- workflow overlay
- role boundary
- handoff behavior
- acceptance criteria

Skill add/remove/install/replace/recompose operations are forbidden in customer production.
