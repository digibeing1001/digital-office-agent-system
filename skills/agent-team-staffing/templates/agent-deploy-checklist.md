# Digital Office Agent Deployment Checklist

Use this checklist before adding or changing a production Digital Office agent.

## Role Definition

- [ ] Agent ID is stable and API-safe.
- [ ] Display name is generic and product-facing.
- [ ] Role, use cases, non-goals, and primary outputs are documented.
- [ ] Human approval boundaries are documented.
- [ ] The role does not duplicate an existing agent.

## Profile Files

- [ ] `profiles/<profile-id>/SOUL.md` exists.
- [ ] `profiles/<profile-id>/config.yaml` exists when runtime defaults are needed.
- [ ] No credentials, local usernames, absolute personal paths, or private notes are present.
- [ ] SOUL content is portable across tenants and deployments.

## Registry

- [ ] `agent-system/agents.registry.json` has the agent entry.
- [ ] `display_name`, `portable_role`, `profile`, `model`, `provider`, and `memory_policy` are set.
- [ ] Routing keywords include representative English and localized terms when appropriate.
- [ ] Route tests cover the common invocation path.
- [ ] Orchestration roles are assigned only when the agent should participate in workflows.

## Verification

- [ ] `scripts/agent-router --health`
- [ ] `scripts/agent-router --route-json "<representative prompt>"`
- [ ] `agent-system/bin/harness-check`
- [ ] Relevant `agent-system/bin/harness-runner --task <task-id> --no-write`
- [ ] `agent-system/tests/smoke.sh`

## Release Notes

- [ ] README or GUI contract is updated when the user-facing capability changes.
- [ ] New approval, notification, or audit behavior is documented.
- [ ] Risks and rollback path are recorded.
