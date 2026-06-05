# Agent Router Registry Configuration

This reference replaces the old hardcoded `AGENTS` dictionary workflow.

## Canonical Source

The canonical router configuration is:

```bash
~/.hermes/agent-system/agents.registry.json
```

The executable router is:

```bash
~/.hermes/scripts/agent-router
```

Do not add new agents by editing a Python dictionary inside `agent-router`. The router must remain a portable executor that reads the registry. This keeps the same agent system migratable across Digital Law Firm, Digital Accounting Firm, Digital Media Studio, and other Digital Office products.

## Registry Shape

Each agent entry should define:

- `id`: stable agent id used by GUI and backend commands
- `profile`: Hermes profile directory name
- `model`: primary model name
- `provider`: provider id
- `aliases`: names users or workflows may use
- `keywords`: routing keywords with weights
- `workflows`: allowed workflow steps
- `route_tests`: prompts that must route to the expected agent

## Add A New Agent

1. Create or copy a sanitized profile template under `~/.hermes/profiles/<profile>/`.
2. Add the agent entry to `~/.hermes/agent-system/agents.registry.json`.
3. Add route tests for the common user phrasing.
4. Run:

```bash
~/.hermes/scripts/agent-router --health
~/.hermes/scripts/agent-router --route-only "<test prompt>"
~/.hermes/scripts/agent-router --route-json "<test prompt>"
```

The tab output of `--route-only` is kept for compatibility:

```text
<agent_id>	<profile>	<model>	<provider>
```

## Call Discipline

All kenny-* agent calls must go through `agent-router` or the Digital Office context command. Do not use direct `delegate_task` for these agents, because it can bypass the selected profile, model, provider, workflow, and route logging.

Recommended:

```bash
~/.hermes/scripts/agent-router --agent pm "<prompt>"
~/.hermes/scripts/agent-router --workflow research_then_plan "<prompt>"
~/.hermes/agent-system/bin/office-system context --project <project_id> --agent <agent_id>
```

Forbidden for kenny-* routing:

```text
delegate_task(profile="kenny-*", ...)
```

## Health Gate

Before packaging or pushing a release, run:

```bash
~/.hermes/scripts/agent-router --health
~/.hermes/agent-system/bin/office-system health
~/.hermes/agent-system/bin/product-update status
```

The release should fail if route tests fail, if the registry cannot be parsed, or if the product update status cannot confirm that production updates are provider-validated rather than direct upstream pulls.
