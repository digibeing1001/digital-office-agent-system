# Digital Office System Bootstrap

This file is the autoload contract for the portable digital-office agent
system. When this file exists under `agent-system/rules/global/`, Hermes or any
compatible runner must treat `agent-system/` as the primary operating layer for
agent routing, knowledge access, project context, and GUI-managed rules.

## Startup Read Order

1. Read `agent-system/agents.registry.json`.
2. Read `agent-system/knowledge.registry.json`.
3. Read `agent-system/rules/rules.registry.json`.
4. Read all active files under `agent-system/rules/global/`.
5. If a project is active, read `agent-system/projects/<project_id>/project.json`,
   then that project's `rules/` and `knowledge/` manifests.
6. If a specialist agent is active, read `agent-system/rules/agents/<agent>.md`
   when present.

## Hard Rules

- Specialist kenny-* agents must be invoked through `agent-system` routing or
  `scripts/agent-router`; do not call them through `delegate_task` or equivalent
  bypass tools.
- The canonical agent list lives in `agent-system/agents.registry.json`.
- The company knowledge base and project knowledge bases are file-backed source
  of truth stores. KeyMemory may index approved summaries, but it is not the raw
  document store.
- GUI-created global, agent, and project rules must be written to the rule
  layer defined in `agent-system/rules/rules.registry.json`.
- Project methodology may enter the company global knowledge base only after a
  draft report is created, shown to the user, and edited or confirmed by the
  user.
- Credentials must never be written to ordinary files or ordinary memory. Use
  environment variables or KeyMemory secret APIs.

## GUI Contract

The GUI should call `agent-system/bin/office-system` for project creation,
knowledge upload, text entries, rule creation, context rendering, methodology
drafting, and methodology approval.
