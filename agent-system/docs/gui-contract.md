# Digital Office GUI Contract

This document defines the GUI-facing contract for the Hermes-based Digital Office layer.

## Product Boundary

- Users see Digital Office, not Hermes internals.
- Hermes runtime, agent profiles, skills, knowledge, rules, memory relay, and local model installers are managed by the product backend.
- Enterprise production updates must come from a provider-validated Digital Office release channel, not direct upstream pulls.
- Enterprise deployments force the GUI as the customer entrypoint. Raw Hermes CLI access is hidden by default and reserved for backend automation or admin-enabled support mode.
- Every backend capability added to this system must have a GUI contract before production release.
- The `secretary` agent id maps to the existing Hermes default secretary loaded from `~/.hermes/SOUL.md`; it is not a second secretary profile.

## Core Commands

All commands are relative to the Hermes home directory.

```bash
~/.hermes/agent-system/bin/product-update status
~/.hermes/agent-system/bin/product-update stage --package <release-package>
~/.hermes/agent-system/bin/office-system health
~/.hermes/scripts/agent-router --route-json "<user request>"
```

GUI state and global settings:

The GUI should use `gui-state` as the home-screen snapshot instead of stitching together files directly.

```bash
~/.hermes/agent-system/bin/office-system gui-state --user <user_id> --project <project_id>
~/.hermes/agent-system/bin/office-system onboarding-options
~/.hermes/agent-system/bin/office-system onboarding-apply --assistant-style neutral_operator --address-style neutral --language auto --initiative-level confirm_before_action --pushback-style risk_based --approval-strictness balanced --memory-mode project_only --work-mode balanced --confirmed
~/.hermes/agent-system/bin/office-system settings-options
~/.hermes/agent-system/bin/office-system settings-status
~/.hermes/agent-system/bin/office-system settings-update --work-mode quality --confirmed
```

- `gui-state` returns health, configured settings, capabilities, Agents, projects, workflows, tasks, approvals, notifications, knowledge, and recent audit records.
- `onboarding-*` is for first-run setup; `settings-*` is for the same preferences after the product is already in use.
- Settings are partial-update friendly: omitted fields keep the previous value, then fall back to the preset default.
- Generated files under `agent-system/settings/` are runtime state and must not be committed.
- Persona preferences never override safety, authorization, approval, knowledge authority, production harness, release, or data-sharing policies.

Router contract:

- The GUI must not hard-code current Agent names as product logic.
- The router returns `agent`, `workflow`, `steps`, `confidence`, `routing_reason`, `workflow_reason`, `candidates`, and `scores`.
- `workflow_reason.source == "workflow_route"` means the task matched a multi-Agent orchestration route.
- `fallback == true` or `clarification_required == true` means the secretary should clarify, reflect, or ask for confirmation before dispatching.
- Workflow steps are resolved from portable `orchestration_roles` in `agents.registry.json`; industry packages may remap those roles to different Agent ids without changing the router code.
- GUI labels should describe the role and workflow to the user, while backend calls use the concrete `agent` and `steps` returned by the router.

Production harness:

```bash
~/.hermes/agent-system/bin/harness-check
~/.hermes/agent-system/bin/harness-runner --task all --no-write
```

- Product, design, and implementation workflows must show gate status before user-facing delivery.
- `pm_to_design` must pass product and design gates.
- `pm_to_design_to_code` must pass product, design, and implementation gates.
- The GUI should show failed gates as rework actions, not as raw CLI errors.
- External high-star skill sources are candidates only. They must be staged, reviewed, adapted, verified, and approved before enterprise use.

Workflow control plane:

The GUI should prefer the workflow control plane for normal users. It creates a workflow run, task inbox item, authorization decision, audit event, and notification in one transaction.

```bash
~/.hermes/agent-system/bin/office-system workflow-start --tenant <tenant_id> --deployment <deployment_id> --user <user_id> --role <role> --project <project_id> --task "<task>"
~/.hermes/agent-system/bin/office-system workflow-status --run-id <run_id>
~/.hermes/agent-system/bin/office-system workflow-list --project <project_id>
~/.hermes/agent-system/bin/office-system workflow-resume --run-id <run_id> --requested-by <user_id> --role <role>
~/.hermes/agent-system/bin/office-system workflow-retry --run-id <run_id> --stage execute --requested-by <user_id> --role <role>
~/.hermes/agent-system/bin/office-system workflow-cancel --run-id <run_id> --requested-by <user_id> --role <role> --confirmed
```

Task inbox:

```bash
~/.hermes/agent-system/bin/office-system task-list --project <project_id>
~/.hermes/agent-system/bin/office-system task-status --task-id <task_id>
~/.hermes/agent-system/bin/office-system task-update --task-id <task_id> --status completed --updated-by <user_id> --role <role>
```

Approval center:

```bash
~/.hermes/agent-system/bin/office-system approval-create --tenant <tenant_id> --deployment <deployment_id> --title "<title>" --action workflow.continue --resource-type workflow_run --resource-id <run_id> --requested-by <user_id> --requested-by-role <role> --approver-role project_manager --workflow-run <run_id> --task-id <task_id>
~/.hermes/agent-system/bin/office-system approval-list --status pending
~/.hermes/agent-system/bin/office-system approval-decision --approval-id <approval_id> --decision approve --decided-by <user_id> --role <role> --confirmed
```

Authorization, audit, and notifications:

```bash
~/.hermes/agent-system/bin/office-system auth-decision --tenant <tenant_id> --deployment <deployment_id> --user <user_id> --role <role> --action workflow.start --resource-type workflow_run --resource-id <run_id> --project <project_id> --agent <agent_id>
~/.hermes/agent-system/bin/office-system audit-events --resource-type workflow_run --resource-id <run_id>
~/.hermes/agent-system/bin/office-system notification-list --user <user_id> --unread-only
~/.hermes/agent-system/bin/office-system notification-mark-read --notification-id <notification_id> --user <user_id>
```

- `workflow-start` is the GUI-safe entrypoint for production work. Raw `loop-start` remains available for lower-level AI-native loop instrumentation.
- `workflow-start` stores the router decision, task, authorization decision, run stages, audit link, and notification link.
- Low-confidence or fallback routes become blocked workflow runs assigned to the secretary for clarification instead of being silently dispatched.
- Approval approve/reject actions and workflow cancel actions require explicit `--confirmed`.
- Audit events are append-only JSONL records with a lightweight hash chain through `previous_event_hash` and `event_hash`.

AI Native Product Loop:

The production loop is Perceive, Plan, Execute, Reflect, Iterate. The GUI should render it as five visible stages rather than a hidden background process.

```bash
~/.hermes/agent-system/bin/office-system loop-start --task "<task>" --project <project_id> --agent <agent_id>
~/.hermes/agent-system/bin/office-system loop-stage --run-id <run_id> --stage perceive --status started
~/.hermes/agent-system/bin/office-system loop-status --run-id <run_id>
~/.hermes/agent-system/bin/office-system iteration-proposal-create --title "<title>" --target workflow --summary "<why>" --expected-impact "<impact>" --risk "<risk>" --rollback "<rollback>"
~/.hermes/agent-system/bin/office-system iteration-proposal-decision --proposal-id <proposal_id> --decision confirm
~/.hermes/agent-system/bin/office-system iteration-proposal-apply --proposal-id <proposal_id> --confirmed --regression-result "<result>"
```

Loop stage labels:

1. Perceive: context, knowledge, permissions, memory relay, route candidates.
2. Plan: role workflow, handoff contract, acceptance criteria, risk, rollback, tests.
3. Execute: Agent dispatch, observations, artifacts, handoffs, gate results.
4. Reflect: findings, root causes, failed gates, reusable methodology drafts.
5. Iterate: explicit improvement proposals only.

Iteration must never be black-box. The GUI must show the proposed change, why it is suggested, expected impact, risk, rollback, affected objects, and regression checks. The only iteration actions are Confirm, Tune Through Conversation, Pause, and Reject. `iteration-proposal-apply` is unavailable unless the proposal was confirmed by the user.

Project lifecycle:

```bash
~/.hermes/agent-system/bin/office-system project-create --project <project_id> --name "<name>"
~/.hermes/agent-system/bin/office-system context --project <project_id> --agent <agent_id>
~/.hermes/agent-system/bin/office-system identity-context --tenant <tenant_id> --deployment <deployment_id> --user <user_id> --role <role> --project <project_id> --agent <agent_id> --workflow-run <run_id>
```

Knowledge:

```bash
~/.hermes/agent-system/bin/office-system knowledge-add --scope company --file <path>
~/.hermes/agent-system/bin/office-system knowledge-add --scope project --project <project_id> --file <path>
~/.hermes/agent-system/bin/office-system knowledge-add-text --scope project --project <project_id> --title "<title>" --body "<text>"
~/.hermes/agent-system/bin/office-system knowledge-source-mount --source-class customer_owned_external_kb --source-id <source_id> --tenant <tenant_id> --deployment <deployment_id> --created-by <user_id> --mount-target project_knowledge --project <project_id>
~/.hermes/agent-system/bin/office-system knowledge-source-mount --source-class provider_sold_industry_kb --source-id <pack_id> --tenant <tenant_id> --deployment <deployment_id> --created-by <user_id> --mount-target licensed_project_reference --project <project_id> --entitlement <entitlement_id>
~/.hermes/agent-system/bin/office-system knowledge-access-log --tenant <tenant_id> --deployment <deployment_id> --user <user_id> --role <role> --project <project_id> --agent <agent_id> --source-class provider_sold_industry_kb --source-id <pack_id> --mount-id <mount_id> --knowledge-pack <pack_id> --entitlement <entitlement_id> --decision allow
```

Online knowledge injection:

- Customer-owned third-party knowledge sources can be synced or indexed into the company knowledge base, project knowledge base, or specialist Agent context.
- Provider-sold industry knowledge products must be mounted as licensed reference layers. They are not copied into company/project source storage.
- Licensed industry knowledge can be queried only inside Digital Office. The GUI must not expose download, export, copy-all, raw source path, or external API access.
- Every licensed industry knowledge query must write an access log identifying tenant, deployment, human user, user role, project, Agent, workflow run, knowledge pack, entitlement, query hash, result source ids, and allow/deny decision.

Rules:

```bash
~/.hermes/agent-system/bin/office-system rule-add --scope global --title "<title>" --body "<rule>"
~/.hermes/agent-system/bin/office-system rule-add --scope agent --agent <agent_id> --title "<title>" --body "<rule>"
~/.hermes/agent-system/bin/office-system rule-add --scope project --project <project_id> --title "<title>" --body "<rule>"
```

Methodology promotion:

```bash
~/.hermes/agent-system/bin/office-system methodology-draft --project <project_id>
~/.hermes/agent-system/bin/office-system methodology-approve --project <project_id> --draft <draft_id>
```

Project relay memory:

```bash
~/.hermes/agent-system/bin/office-system relay-add --project <project_id> --agent <agent_id> --title "<title>" --body "<summary>"
```

RAG:

```bash
~/.hermes/agent-system/bin/office-system rag-index --scope project --project <project_id>
~/.hermes/agent-system/bin/office-system rag-search --scope project --project <project_id> --query "<query>"
```

Data sharing:

```bash
~/.hermes/agent-system/bin/office-system telemetry-status
~/.hermes/agent-system/bin/office-system telemetry-export
~/.hermes/agent-system/bin/office-system telemetry-send --bundle <exported_bundle> --confirmed
```

New Agent plugin request:

```bash
~/.hermes/agent-system/bin/office-system agent-request-submit --title "<request>" --body "<approved requirement>" --confirmed
~/.hermes/agent-system/bin/office-system agent-request-status --request-id <request_id>
```

Existing Agent improvement, limited to SOUL/workflow only:

```bash
~/.hermes/agent-system/bin/office-system agent-improvement-draft --agent <agent_id> --kind soul --title "<title>" --body "<approved change>"
~/.hermes/agent-system/bin/office-system agent-improvement-draft --agent <agent_id> --kind workflow --title "<title>" --body "<approved change>"
~/.hermes/agent-system/bin/office-system agent-improvement-approve --agent <agent_id> --draft <draft_id> --confirmed
```

Downloaded Agent plugin package:

```bash
~/.hermes/agent-system/bin/office-system agent-plugin-report --package <package_dir> --request-id <request_id> --project <project_id>
~/.hermes/agent-system/bin/office-system agent-plugin-decision --report-id <report_id> --decision confirm
~/.hermes/agent-system/bin/office-system agent-plugin-decision --report-id <report_id> --decision tune --message "<user tuning note>"
~/.hermes/agent-system/bin/office-system agent-plugin-decision --report-id <report_id> --decision pause --message "<optional reason>"
~/.hermes/agent-system/bin/office-system agent-plugin-activate --package <package_dir> --report-id <report_id> --request-id <request_id> --project <project_id> --confirmed
```

## Knowledge And Memory Priority

Fact authority:

1. Project knowledge base
2. Company global knowledge base
3. Licensed industry reference layer
4. KeyMemory relay and semantic memory

Handoff authority:

1. Current task state
2. KeyMemory project relay
3. Latest project decisions
4. Company global methods

Rule priority:

1. System bootstrap rules
2. Company global rules
3. Project rules
4. Agent rules
5. Task instructions

KeyMemory should help agents continue work across sessions, agents, and subprojects. It should not override source documents, approved company knowledge, licensed industry reference access policy, or explicit project decisions.

## Team And Permissions

The GUI must treat Digital Office as a team workspace even when a deployment has only one real human user.

Required future surfaces:

1. Team Members
2. Roles and Permissions
3. Project Members
4. Agent Delegation
5. Knowledge Access Logs
6. Seat and Entitlement Usage
7. Support Access

Human users and Agent workers are separate identities. A human user can delegate work to an Agent only when the user has project permission and the Agent is on the project roster. Professional outputs, such as legal, tax, accounting, or regulated advice, require a human reviewer role before final delivery.

## Multimodal Knowledge

The GUI can upload PDF, Word, text, and images. The backend stores raw files locally and extracts searchable text.

- Text and DOCX extraction should run locally.
- PDF extraction should run locally with `pdftotext` or `pypdf`.
- OCR should run locally with Tesseract or RapidOCR after deployment.
- Vision LLM fallback is allowed only when local OCR is low-confidence or the image requires visual understanding beyond text.

Model weights are not stored in this repository. They are downloaded to the enterprise host by `agent-system/bin/install-local-models`.

## Enterprise Updates

The GUI update button should say "Check for product updates". It should not expose "Hermes update" or "skill update" to ordinary users.

The provider release flow is:

1. Build candidate release including Hermes runtime, Digital Office agent system, profiles, skills, GUI, and installers.
2. Pin component versions and run health, router, knowledge, RAG, and GUI smoke tests.
3. Sign and publish the release manifest.
4. Let enterprise administrators stage, review, and schedule installation.
5. Backup current deployment, install atomically, verify, and allow rollback.

## Secretary Agent Staffing

The secretary Agent should help users clarify new digital employee needs, but it must not create production Agents autonomously.

Customer-visible request statuses:

1. 接收需求
2. 正在推动需求
3. 已完成需求
4. 已下载部署

The flow is:

1. Secretary notices a gap or the user asks for a new Agent.
2. Secretary clarifies the request through conversation and asks the user to submit.
3. `agent-request-submit` sends the approved requirement to the provider backend.
4. Provider staff design, test, and publish an Agent plugin package.
5. The customer host downloads the package.
6. Secretary immediately shows an integration report describing how the new Agent will enter the current system and workflows.
7. The GUI shows three actions: Confirm, Tune Through Conversation, Pause.
8. Only Confirm moves the report to `confirmed_for_activation`; registration and deployment must include that `report_id`. Tune updates the report through dialogue. Pause keeps the task suspended.

Existing Agents may be improved through conversation, but only by updating SOUL/workflow overlays. Customer production must not add, remove, install, or recompose skills. Skill bundles belong to provider-validated Agent plugin packages.
