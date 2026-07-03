# Digital Office GUI Contract

This document defines the GUI-facing contract for the Hermes-based Digital Office layer.

## Product Boundary

- Users see Digital Office, not Hermes internals.
- Hermes runtime, agent profiles, skills, knowledge, rules, memory relay, and local model installers are managed by the product backend.
- Enterprise production updates must come from a provider-validated Digital Office release channel, not direct upstream pulls.
- The GUI is the intended customer entrypoint after a deployment is promoted to the pilot or stable channel. Raw Hermes CLI access is hidden by default and reserved for backend automation or admin-enabled support mode.
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

- `gui-state` returns health, configured settings, capabilities, Agents, digital employees, workflow packs, context contract, local skill installations, projects, workflows, tasks, approvals, notifications, knowledge, and recent audit records.
- `onboarding-*` is for first-run setup; `settings-*` is for the same preferences after the product is already in use.
- Settings are partial-update friendly: omitted fields keep the previous value, then fall back to the preset default.
- Generated files under `agent-system/settings/` are runtime state and must not be committed.
- Persona preferences never override safety, authorization, approval, knowledge authority, production harness, release, or data-sharing policies.

Web UI and PWA applications:

The release contains two entrypoints backed by one control plane. `/` is the ordinary user application. `/admin` is the administration center. They share authentication, GUI state, authorization, audit, design components, and API contracts, but keep separate navigation and operational responsibilities. Mutating workflow, approval, and Agent actions call narrow governed API routes with the same authorization, audit, and confirmation rules as the CLI control plane.

```bash
~/.hermes/agent-system/bin/office-system web-config --public-url https://office.example.com
~/.hermes/agent-system/bin/office-system web-serve --host 127.0.0.1 --port 8787 --public-url https://office.example.com --quiet
```

Browser routes:

- `GET /api/health`
- `GET /api/gui-state`
- `GET /api/web-app`
- `GET /manifest.webmanifest`
- `GET /service-worker.js`
- `POST /api/workflows`
- `POST /api/projects`
- `POST /api/knowledge/uploads`
- `POST /api/agents`
- `POST /api/agents/{agent_id}/status`
- `DELETE /api/agents/{agent_id}?confirmed=true`
- `POST /api/approvals/{approval_id}/decision`

Agent lifecycle rules:

- Only authorized administration roles can create or change custom Agents.
- Custom Agents must be created from an approved built-in template.
- Built-in Agents are protected from lifecycle edits and deletion.
- Permanent deletion requires an archived Agent and explicit confirmation.
- Tasks, artifacts, and audit history remain addressable after the Agent configuration is deleted.

Deployment guidance:

- Use `agent-system/deploy/Caddyfile.example`, `agent-system/deploy/nginx.conf.example`, or `agent-system/deploy/systemd/digital-office-web.service.example` as customer-site templates.
- Bind `web-serve` to `127.0.0.1` behind Caddy/Nginx for internet-facing deployments.
- Bind to `0.0.0.0` only on trusted LAN/VPN networks.
- PWA installation requires HTTPS in normal browsers, except localhost during local development.
- Do not expose a generic remote shell, CLI executor, or arbitrary command endpoint to the Web UI.

Router contract:

- The GUI must not hard-code current Agent names as product logic.
- The router returns `agent`, `workflow`, `steps`, `confidence`, `routing_reason`, `workflow_reason`, `candidates`, and `scores`.
- `workflow_reason.source == "workflow_route"` means the task matched a multi-Agent orchestration route.
- `fallback == true` or `clarification_required == true` means the secretary should clarify, reflect, or ask for confirmation before dispatching.
- Workflow steps are resolved from portable `orchestration_roles` in `agents.registry.json`; industry packages may remap those roles to different Agent ids without changing the router code.
- GUI labels should describe the role and workflow to the user, while backend calls use the concrete `agent` and `steps` returned by the router.
- Business department wording is a UI mental model, not a third Agent layer. The backend contract is `secretary -> digital employee Agent -> Skill staff lanes`.
- `agent-system/digital-employees.registry.json` describes product-visible digital employees. `agent-system/workflow-packs.registry.json` describes workflow ids, owning Agents, Skill lanes, source packs, and delivery gates.
- `agent-system/context-envelope.schema.json` is the context handoff contract. Large documents move by artifact refs; decisions, assumptions, open questions, and risk flags must stay structured.
- `agent-system/context-handoff.policy.json` defines stable context/task/handoff identity, transfer modes, recipient acknowledgment, status transitions, security boundaries, and quality metrics.
- `agent-system/skill-installations.registry.json` records locally installed source packs and license-blocked candidates.
- The legal UI should show one enterprise Digital Lawyer. Contract review, compliance review, privacy review, employment/IP review, dispute triage, and AI governance are internal Skill lanes under that Agent.
- Digital Lawyer workflows are internal review drafts. The GUI must show source verification status and human review gates before any user relies on legal output, sends external communications, approves launch, approves signature, or takes regulated action.

Production harness:

```bash
~/.hermes/agent-system/bin/harness-check
~/.hermes/agent-system/bin/harness-runner --task all --no-write
```

- Product, design, and implementation workflows must show gate status before user-facing delivery.
- `pm_to_design` must pass product and design gates.
- `pm_to_design_to_code` must pass product, design, and implementation gates.
- `legal_*` workflows must pass Digital Lawyer routing, local skill installation, source-policy, and human-review guardrail gates.
- The GUI should show failed gates as rework actions, not as raw CLI errors.
- External high-star skill sources are candidates only. They must be staged, reviewed, adapted, verified, and approved before enterprise use.

Workflow control plane:

The GUI should prefer the workflow control plane for normal users. It creates a workflow run, task inbox item, authorization decision, audit event, and notification in one transaction.

```bash
~/.hermes/agent-system/bin/office-system workflow-start --tenant <tenant_id> --deployment <deployment_id> --user <user_id> --role <role> --project <project_id> --task "<task>"
~/.hermes/agent-system/bin/office-system workflow-status --run-id <run_id>
~/.hermes/agent-system/bin/office-system workflow-list --project <project_id>
~/.hermes/agent-system/bin/office-system workflow-resume --run-id <run_id> --requested-by <user_id> --role <role>
~/.hermes/agent-system/bin/office-system workflow-retry --run-id <run_id> --stage act --requested-by <user_id> --role <role>
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

Human judgment gates:

These gates are not ordinary approval buttons. They are runtime stops raised by
Agent self-checks or deterministic policy checks before the system continues
high-risk, ambiguous, externally visible, or evidence-sensitive work.

```bash
~/.hermes/agent-system/bin/office-system judgment-evaluate --task "<task>" --stage decide --agent <agent_id>
~/.hermes/agent-system/bin/office-system judgment-list --status pending
~/.hermes/agent-system/bin/office-system judgment-decision --case-id <case_id> --decision approve --decided-by <user_id> --role <required_role> --confirmed
~/.hermes/agent-system/bin/office-system judgment-resume --run-id <run_id> --requested-by <user_id> --role <role>
```

- `workflow-start`, `agent-invoke`, and `loop-start` evaluate judgment policy before dispatch.
- Open judgment cases put the workflow and linked tasks into `waiting_human_judgment`.
- `workflow-resume`, `workflow-retry`, `task-update --status completed`, and `loop-stage` must not bypass an open judgment case.
- The GUI should show the risk, triggers, blocked actions, evidence references, recommended option, and required human role before rendering decision buttons.
- A human decision writes a `digital-office-judgment-case` record plus an audit event; Agent-generated stop signals cannot delete or approve their own cases.

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

Runtime replay, checkpoints, coordination, and typed handoff:

These commands are production control-plane commands, not hidden debug tools. The GUI may present them in an orchestration or workbench surface so operators can understand why a run chose a topology, where it can resume, and what each Agent received from the previous Agent.

```bash
~/.hermes/agent-system/bin/office-system coordination-plan --task "<task>" --agent researcher --agent writer --parallelizable
~/.hermes/agent-system/bin/office-system run-ledger-list --run-id <run_id>
~/.hermes/agent-system/bin/office-system checkpoint-create --run-id <run_id> --stage decide --label "<label>" --resume-cursor decide:ready
~/.hermes/agent-system/bin/office-system checkpoint-list --run-id <run_id>
~/.hermes/agent-system/bin/office-system handoff-create --run-id <run_id> --from-agent researcher --to-agent writer --reason "<reason>" --acceptance-criterion "<criterion>"
~/.hermes/agent-system/bin/office-system handoff-list --run-id <run_id>
~/.hermes/agent-system/bin/office-system eval-run --suite runtime-replay-and-multilingual --no-write
```

- `coordination-plan` chooses one of the modes defined in `coordination.policy.json`; high-risk modes require human judgment before execution.
- `run-ledger-list` exposes the hash-chained run trace. The GUI should show event, stage, action, artifact refs, checkpoint id, handoff id, and hashes.
- `checkpoint-create` stores a resumable state snapshot. Use `--requires-human --create-judgment` when the checkpoint itself should stop the workflow for human decision.
- `handoff-create` is required for cross-Agent transfer of responsibility. It stores the source Agent, target Agent, schema hash, context hash, artifacts, and acceptance criteria.
- `eval-run` returns a deterministic pass/fail report and should be shown before production delivery claims.

Direct `@Agent` invocation:

The chat UI may let users address a specific Agent, for example `@coder implement this API`. This is still a governed workflow entrypoint. The GUI must call `agent-invoke`, not bypass the control plane.

```bash
~/.hermes/agent-system/bin/office-system agent-invoke --tenant <tenant_id> --deployment <deployment_id> --user <user_id> --role <role> --project <project_id> --agent <agent_id> --task "<task>"
```

Successful output includes `agent_id`, `project_id`, `requested_by`, `invocation_mode=direct_agent`, `workflow_run_id`, `task_id`, `active_revision_id`, `authorization`, and `audit_event_id`. A denied call returns a structured JSON denial or non-zero validation error for unknown Agent, missing project, missing project roster membership, or insufficient user role.

Workflow canvas revisions and runtime controls:

The workflow canvas is a constrained office workflow editor, not an unrestricted low-code platform. Edits to future workflow structure must use draft revisions. Completed nodes cannot be rewritten in place.

```bash
~/.hermes/agent-system/bin/office-system workflow-draft-create --run-id <run_id> --created-by <user_id> --role <role>
~/.hermes/agent-system/bin/office-system workflow-draft-patch --run-id <run_id> --revision-id <revision_id> --updated-by <user_id> --role <role> --patch-json '<json>'
~/.hermes/agent-system/bin/office-system workflow-draft-validate --run-id <run_id> --revision-id <revision_id>
~/.hermes/agent-system/bin/office-system workflow-draft-activate --run-id <run_id> --revision-id <revision_id> --activated-by <user_id> --role <role> --confirmed
~/.hermes/agent-system/bin/office-system workflow-node-context --run-id <run_id> --node-id <node_id>
~/.hermes/agent-system/bin/office-system workflow-control --run-id <run_id> --action run|pause|resume|stop --requested-by <user_id> --role <role>
```

Canvas component types reserved for GUI:

- `agent_task`
- `text_instruction`
- `file_ref`
- `folder_ref`
- `knowledge_scope`
- `approval_gate`
- `human_input`
- `output_artifact`
- `merge_summary`
- `condition`
- `parallel_group`

Simple mode should expose only Agent, text, file/folder/knowledge, approval, and output. Professional/admin modes may expose condition, merge, parallel, and human input components.

Validation rules:

- A runnable canvas must have a start node and a final `output_artifact`.
- No isolated or unreachable nodes.
- Ordinary cycles are rejected. Future loop components must declare exit condition and max iterations before they become runnable.
- Agent nodes require both `agent_id` and instruction text.
- File/folder/knowledge nodes require concrete ids or scopes.
- Edges must connect compatible input/output types.
- High-risk Agent nodes must have a downstream `approval_gate`.
- `workflow-node-context` always reads the current active revision. If an Agent tries to use a stale revision id, the command returns `stale_revision`.

Runtime controls:

- `pause` records `pause_requested` and pauses after the current node finishes.
- `resume` or `run` clears the pause request and restores the current stage status.
- `stop` requires `--confirmed` and cancels queued/running linked tasks.
- Completed, cancelled, or stopped workflows cannot be rewritten or controlled.

AI Native Product Loop:

The production runtime has four composable work nodes: Context, Decide, Act, Evaluate. A deterministic backend controller owns transitions. The GUI renders durable backend state and never invents a client-side transition.

```bash
~/.hermes/agent-system/bin/office-system loop-start --task "<task>" --project <project_id> --agent <agent_id>
~/.hermes/agent-system/bin/office-system loop-stage --run-id <run_id> --stage context --status started
~/.hermes/agent-system/bin/office-system loop-usage-add --run-id <run_id> --tool-calls 1 --model-calls 1
~/.hermes/agent-system/bin/office-system loop-control --run-id <run_id> --decision complete --progress-score 1 --acceptance-passed
~/.hermes/agent-system/bin/office-system loop-status --run-id <run_id>
~/.hermes/agent-system/bin/office-system iteration-proposal-create --title "<title>" --target workflow --summary "<why>" --expected-impact "<impact>" --risk "<risk>" --rollback "<rollback>"
~/.hermes/agent-system/bin/office-system iteration-proposal-decision --proposal-id <proposal_id> --decision confirm
~/.hermes/agent-system/bin/office-system iteration-proposal-apply --proposal-id <proposal_id> --confirmed --regression-result "<result>"
```

Work node labels:

1. Context: authoritative context, permissions, provenance, unknowns, artifact references, and context budget.
2. Decide: structured decision record, route or plan, acceptance criteria, risk, rollback, and next action. Private chain-of-thought is never stored or displayed.
3. Act: Agent and Skill dispatch, idempotent side effects, observations, artifacts, typed handoffs, acknowledgments, checkpoints, and usage.
4. Evaluate: evidence-backed acceptance results, progress, failure class, budget, and one recommended controller decision.

Controller decisions are `continue`, `replan`, `retry`, `wait_human`, `complete`, `fail`, `cancel`, and `budget_exhausted`. The UI must expose current cycle, configured budgets, usage, progress score, last decision, blockers, and waiting reason. Simple tasks may show Decide as skipped only when the backend records the reason.

Typed handoff UI must distinguish `pending_acceptance`, `needs_context`, `accepted`, and `rejected`. The recipient must verify `context_hash` before calling `handoff-ack`; pending or missing-context delivery is not complete.

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

Browser upload route:

```bash
POST /api/knowledge/uploads
```

The Web route accepts text or file content, writes it through the governed knowledge commands, and records an audit event. Project uploads should be the default for normal work because every project folder is the context container for its own conversations, materials, approvals, records, and deliverables.

Knowledge spaces, folders, and ACL:

The GUI should use knowledge spaces for fine-grained folder and file control. Supported spaces are `personal`, `project`, `team`, `company`, `workflow_artifacts`, and virtual `shared_with_me`.

```bash
~/.hermes/agent-system/bin/office-system knowledge-folder-create --space-type personal --owner <user_id> --folder-id <folder_id> --title "<title>" --created-by <user_id> --role <role>
~/.hermes/agent-system/bin/office-system knowledge-item-add --space-type personal --owner <user_id> --folder-id <folder_id> --item-id <item_id> --title "<title>" --source-ref <ref> --created-by <user_id> --role <role>
~/.hermes/agent-system/bin/office-system knowledge-share --space-type personal --owner <owner_id> --resource-type folder --resource-id <folder_id> --target-type user|role|agent|project|workflow --target-id <target_id> --shared-by <owner_id> --role <role>
~/.hermes/agent-system/bin/office-system knowledge-access-check --space-type personal --owner <owner_id> --resource-type item --resource-id <item_id> --user <user_id> --role <role> --agent <agent_id>
~/.hermes/agent-system/bin/office-system knowledge-scope-resolve --space-type project --project <project_id> --folder-id <folder_id> --user <user_id> --role <role>
~/.hermes/agent-system/bin/office-system knowledge-tree --space-type shared_with_me --user <user_id> --role <role>
```

- Personal folders are private by default.
- A personal file or folder can be shared to a user, role, Agent, project, or workflow scope.
- Explicit deny shares override allow shares.
- Folder grants inherit to child folders and items unless `--no-inherit` is used.
- `knowledge-scope-resolve` defaults to snapshot mode so workflow runs are reproducible. Use `--live-mode` only as an advanced explicit choice.
- Every access check and scope resolution writes `knowledge_acl_access` to `logs/knowledge-access.jsonl`.

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

Collaborative rule intake:

Users will not know every production rule at onboarding time. The GUI should
let Agents ask focused questions during collaboration and turn user-stated
preferences into reviewable rule proposals.

```bash
~/.hermes/agent-system/bin/office-system rule-elicit --project <project_id> --agent <agent_id> --context "<current collaboration context>"
~/.hermes/agent-system/bin/office-system rule-suggest --title "<rule title>" --body "<rule in user's words>" --project <project_id> --agent <agent_id> --source conversation --created-by <user_id>
~/.hermes/agent-system/bin/office-system rule-proposal-list --status pending_user_confirmation
~/.hermes/agent-system/bin/office-system rule-proposal-decision --proposal-id <proposal_id> --decision approve --decided-by <user_id> --role project_manager --scope global|project|agent --confirmed
```

- `rule-elicit` returns conversational prompts for missing production-rule areas such as human judgment, evidence standards, role boundaries, quality bars, and data boundaries.
- `rule-suggest` creates a pending proposal, not an active rule. It infers whether the rule belongs to global, project, or Agent scope and exposes alternatives when confidence is low.
- `rule-proposal-decision --decision approve --confirmed` is the only path that writes the rule into the active rule store.
- Scope classification is advisory. The human can override the proposed scope before approval.
- Agent-specific rules belong under `rules/agents/<agent>.md`; project/client rules belong under `projects/<project_id>/rules`; company-wide safety, approval, memory, and knowledge-promotion rules belong under `rules/global`.

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

Role workbenches:

The home page can show a universal project board, but role-specific workbenches should be available for focused work. Use `workbench-state` to populate those pages.

```bash
~/.hermes/agent-system/bin/office-system workbench-state --tenant <tenant_id> --deployment <deployment_id> --user <user_id> --role owner
~/.hermes/agent-system/bin/office-system workbench-state --tenant <tenant_id> --deployment <deployment_id> --user <user_id> --role project_manager --project <project_id>
~/.hermes/agent-system/bin/office-system workbench-state --tenant <tenant_id> --deployment <deployment_id> --user <user_id> --role member --project <project_id>
~/.hermes/agent-system/bin/office-system workbench-state --tenant <tenant_id> --deployment <deployment_id> --user <user_id> --role professional_reviewer --project <project_id>
```

Returned views include `owner_global`, `project_lead`, `member`, `approver`, and `viewer`. Owners see global project health, blockers, cost/load placeholders, pending approvals, knowledge spaces, and system health. Project leads see project progress, team tasks, blockers, and project knowledge. Members see their tasks and workflows. Approvers see pending review queues. Viewers see read-only project/output summaries.

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
