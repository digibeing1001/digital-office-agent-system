# Enterprise Release Design

Customers should experience this as the Digital Office product. They do not
need to know that Hermes is the underlying runtime.

## Customer-Facing Surface

Show:

- projects
- digital employees
- company knowledge base
- project knowledge base
- rules and approvals
- task status and deliverables
- product version and health
- new Agent request status
- downloaded Agent plugin integration report
- confirm, tune, and pause actions before a new Agent enters workflows

Hide by default:

- Hermes internals
- provider names
- raw router details
- skill repository details
- low-level update mechanics
- raw Hermes command-line interface

Support mode may expose runtime diagnostics to administrators.

The enterprise customer entrypoint is GUI-only. Raw Hermes CLI access is an
internal backend/support tool and must be hidden from ordinary users.

## Update Philosophy

Enterprise production should not update Hermes or skills live from upstream
repositories. Updates should be validated by us first, packaged into a release,
then offered to customer administrators through our channel.

Digital Office releases may include the Hermes runtime itself. In production,
Hermes is treated as an internal runtime component, not as a customer-facing
product surface. The release artifact should therefore bundle or pin:

- Hermes runtime version
- Digital Office agent-system version
- agent registry and workflow registry
- profile templates and skill bundles
- GUI build version
- local model installer manifest
- migration scripts and rollback metadata

Recommended flow:

1. Internal experiment.
2. Automated checks: router, workflows, knowledge ingestion, RAG, telemetry.
3. Pilot deployment.
4. Stable release manifest.
5. Customer admin approves install window.
6. System creates rollback snapshot.
7. Switch active version.

The GUI button should say `Check for product updates`, not `Update Hermes`.

## New Agent Delivery

New production Agents are delivered as provider-designed Agent plugin packages.
The customer-site secretary Agent does not autonomously generate production
Agents and does not add, remove, install, or recompose skills.

Flow:

1. User discusses a new Agent need with the secretary Agent.
2. Secretary clarifies the business problem, expected work, constraints, and
   success criteria.
3. User confirms and submits the requirement to the provider backend.
4. Provider staff design, test, and package the Agent.
5. The package is pushed through the validated product update channel.
6. After download, the secretary Agent immediately shows an integration report.
7. User chooses Confirm, Tune Through Conversation, or Pause.
8. Only Confirm registers the Agent and adds it to the selected workflow/project.

Customer-visible status labels:

1. 接收需求
2. 正在推动需求
3. 已完成需求
4. 已下载部署
