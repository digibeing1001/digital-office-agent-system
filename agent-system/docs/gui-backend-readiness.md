# GUI Backend Readiness Design

This backend is preparing for a commercial Digital Office GUI. Version 1 intentionally does not draw the GUI yet. It reserves stable commands, JSON state, validation, audit, and harness coverage so the frontend can be built on durable contracts.

## Product Constraint

Digital Office is a constrained office workflow orchestrator, not an open-ended low-code platform.

The canvas exists so users can understand and adjust an office workflow. It should guide them toward safe structure, enforce permissions, and prevent accidental unbounded automation. Advanced graph editing belongs behind professional/admin modes.

## Research Anchors

The backend design follows these product lessons:

- Copilot Studio: Agents can be workflow nodes with knowledge sources.
- ServiceNow Workflow Studio and Salesforce Agentforce: enterprise workflows need governance, identity, audit, and approvals.
- Zapier Canvas: users benefit from a visual system map and AI-assisted edits.
- n8n: execution history, pause/resume, and run state must be separate from workflow definitions.
- Flowise and Dify: human-in-the-loop steps need explicit context and state.
- Asana and monday.com: executives and operators need different dashboard summaries.
- Google Drive, Box, SharePoint, and Notion: knowledge access needs folder hierarchy, inheritance, explicit shares, and audit trails.

Reference URLs are tracked in the implementation plan and README rather than copied into runtime state.

## Backend Contracts Added For GUI

- `agent-invoke`: direct `@Agent` dispatch without bypassing workflow governance.
- Workflow revisions: `workflow-draft-create`, `workflow-draft-patch`, `workflow-draft-validate`, `workflow-draft-activate`.
- Workflow runtime controls: `workflow-control --action run|pause|resume|stop`.
- Node execution context: `workflow-node-context`, always reading the active revision.
- Knowledge spaces: personal, project, team, company, workflow artifact, and shared-with-me views.
- Knowledge ACL: folder hierarchy, item/folder grants, inheritance, explicit deny, user/role/Agent/project/workflow targets, and access logs.
- Role workbench state: owner, project lead, member, approver, viewer.

## Canvas Safety Rules

- Draft revisions do not affect active runs until validated and confirmed.
- Invalid revisions cannot be activated.
- Completed nodes cannot be edited in place.
- A valid workflow must have start and final output nodes.
- No unreachable nodes.
- No ordinary cycles.
- Agent nodes need an Agent id and instruction.
- High-risk Agent nodes need downstream approval.
- Edges must connect compatible data types.

## UX Implications

- Default canvas mode should be simple: Agent, text instruction, file/folder/knowledge, approval, output.
- Advanced condition, merge, human input, and parallel components should be gated behind professional/admin modes.
- GUI edits should show validation errors inline before activation.
- Stopping a workflow should require a destructive confirmation.
- Knowledge scope resolution should default to snapshot mode for reproducible runs.
- Personal folders are private by default and should not appear in ordinary admin dashboards unless explicitly shared or accessed through support/legal procedure outside normal product UI.

## Verification Gates

The following harness tasks must pass before GUI work builds on this backend:

- `direct-agent-invocation-production`
- `workflow-canvas-revision-production`
- `knowledge-space-acl-production`
- `role-workbench-production`

They are also required by `harness-check`.
