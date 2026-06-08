# Agent Router Configuration Reference

The Digital Office router maps user intent to agent IDs, profiles, providers, and workflow roles.

## Required Registry Fields

- `display_name`: user-facing name shown in GUI and logs.
- `portable_role`: short capability label for cross-deployment mapping.
- `profile`: profile directory under `profiles/`, or `__default__` for the default secretary entrypoint.
- `model` and `provider`: non-secret runtime selection.
- `memory_policy`: memory backend policy.
- `routing.default_workflow`: default workflow when no multi-agent workflow route applies.
- `routing.keywords`: weighted routing terms.
- `orchestration_roles`: roles the agent may fulfill in workflows.

## Routing Rules

- Prefer role-based workflows for multi-step work.
- Keep fallback behavior explicit and visible to the GUI.
- Route tests must verify common prompts and ambiguity handling.
- Direct delegation must not bypass registry routing, audit events, approvals, or project roster checks.

## Verification

Run:

```bash
scripts/agent-router --health
scripts/agent-router --route-json "product requirement design ui prototype code implement frontend"
agent-system/bin/harness-check
```
