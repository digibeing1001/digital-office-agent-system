# Skill Installation Pattern

Use this pattern when an agent needs an additional reusable skill.

## Rules

- Prefer existing product skills before adding new ones.
- Keep skill installation auditable and reversible.
- Do not store credentials or private source URLs in the repository.
- New production skills require user-visible confirmation and verification.

## Steps

1. Define why the skill is needed and which agent uses it.
2. Add the skill under `skills/<skill-id>/`.
3. Add concise public documentation in `SKILL.md`.
4. Update `agent-system/agents.registry.json` for affected agents.
5. Add or update route tests or harness gates when behavior changes.
6. Run router, harness, and smoke verification.

## Verification

```bash
scripts/agent-router --health
agent-system/bin/harness-check
agent-system/tests/smoke.sh
```
