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

Project lifecycle:

```bash
~/.hermes/agent-system/bin/office-system project-create --project <project_id> --name "<name>"
~/.hermes/agent-system/bin/office-system context --project <project_id> --agent <agent_id>
```

Knowledge:

```bash
~/.hermes/agent-system/bin/office-system knowledge-add --scope company --file <path>
~/.hermes/agent-system/bin/office-system knowledge-add --scope project --project <project_id> --file <path>
~/.hermes/agent-system/bin/office-system knowledge-add-text --scope project --project <project_id> --title "<title>" --body "<text>"
```

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
~/.hermes/agent-system/bin/office-system agent-plugin-activate --package <package_dir> --request-id <request_id> --project <project_id> --confirmed
```

## Knowledge And Memory Priority

Fact authority:

1. Project knowledge base
2. Company global knowledge base
3. KeyMemory relay and semantic memory

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

KeyMemory should help agents continue work across sessions, agents, and subprojects. It should not override source documents, approved company knowledge, or explicit project decisions.

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
8. Only Confirm runs registration and deployment. Tune updates the report through dialogue. Pause keeps the task suspended.

Existing Agents may be improved through conversation, but only by updating SOUL/workflow overlays. Customer production must not add, remove, install, or recompose skills. Skill bundles belong to provider-validated Agent plugin packages.
