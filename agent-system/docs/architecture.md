# Digital Office Agent System Architecture

## Goal

This layer turns a compatible Agent host into a portable Digital Office runtime.
It should work as an experiment inside `~/.hermes` today, inject into clean
Hermes or OpenClaw installations, and later migrate into products such as
Digital Law Firm, Digital Accounting Firm, or Digital Media Studio.

## Runtime Layers

1. Digital Office GUI
2. Product backend API
3. tenant identity, roles, seats, and entitlement control
4. Agent host runtime such as Hermes or OpenClaw
5. `agent-system` registries and policies
6. department namespaces and workflow packs
7. agent profiles and skills
8. company/project knowledge bases
9. licensed industry reference layer
10. KeyMemory relay and semantic memory
11. local model capabilities for OCR and RAG

The GUI should expose projects, digital employees, knowledge, rules, approvals,
and product updates. It should not expose host runtime internals by default.

## Host Rule Injection

`agent-system/host-injection.policy.json` is the canonical policy for installing
Digital Office into clean and non-clean Agent hosts.

Clean hosts receive the Digital Office managed entrypoint automatically. The
host default Agent is injected as the `secretary` Agent and must load
`agent-system/` rules, registries, workflows, gates, and release policy before
host-local defaults.

Non-clean hosts are never silently overwritten. If the installer finds unmanaged
`SOUL.md`, unmanaged `AGENTS.md`, user preferences, projects, knowledge, tasks,
or run state, it must require one of two explicit choices:

1. Preserve existing host rules and install Digital Office side-by-side.
2. Back up the existing host entrypoint and overwrite it with the Digital Office
   secretary entrypoint.

Hermes uses `SOUL.md` as the injected default Agent entrypoint. OpenClaw and
generic compatible hosts use `AGENTS.md`.

## Team And Identity

The first experiment can run as a single-user Digital Office, but the product
must be designed as a team workspace from the beginning.

Human users and Agent workers are separate identities:

- human users hold tenant, project, approval, billing, and knowledge permissions
- Agent workers execute tasks only when delegated by an authorized human user or
  workflow
- support operators are provider-side identities and require explicit,
  time-limited admin approval

Every workflow run should carry these claims:

1. tenant id
2. deployment id
3. human user id and role
4. project id
5. Agent id
6. workflow run id
7. entitlement ids used during the run

This lets multiple real employees use the same Digital Office later without
rewriting the Agent runtime.

## Departments

Departments are first-class product concepts, but they are not rigid simulated
human management hierarchies. A department is a capability namespace, permission
boundary, knowledge space, workflow bundle, and user-facing mental model.

The runtime should still choose the smallest useful topology:

1. Direct specialist when one capability can handle the task.
2. Department workflow when a domain task needs several capability lanes.
3. Department lead synthesis only for intake, conflict resolution, final
   business-facing summary, escalation, and approval gates.

`agent-system/departments.registry.json` records department metadata, lead
agents, specialist agents, workflow ids, knowledge scopes, source skill packs,
and safety policy. It does not replace `agents.registry.json`; it adds an
organization layer above role and workflow routing.

The first implemented department is `legal`, an enterprise legal department.
It models in-house legal support rather than a law firm team. Legal outputs are
internal review drafts, not final legal opinions. External reliance, filings,
contract signature approval, product launch approval, employment action, demand
letters, and litigation steps require human professional review.

## Agent Routing

`agent-system/agents.registry.json` is the canonical agent roster. It defines
agents, profiles, models, providers, route keywords, workflows, and route tests.

`scripts/agent-router` is only the executor. It reads the registry, resolves an
agent or workflow, logs route events without storing raw prompts, and launches
Hermes with the selected profile/model/provider.

Routing stays role-first. A request may mention a department, but the router
resolves it into portable orchestration roles and concrete workflow steps. For
example, a legal contract review resolves to legal intake, contract review, and
legal synthesis rather than blindly simulating a chain of human managers.

The `secretary` agent id refers to the current host default Agent entrypoint
after Digital Office injection. It must not be duplicated as a second
customer-facing secretary profile. In the registry, `profile: "__default__"`
means the router omits a specialist profile and lets the host use the default
secretary entrypoint.

This split is required for migration. A law firm package, accounting package,
and media studio package can ship different registries while reusing the same
router.

## Knowledge And Memory

Company global knowledge base:

- stores approved organization-level methods, templates, standards, and reusable
  domain experience
- can be reused across projects
- should be promoted from project work only after user review and approval

Project knowledge base:

- stores active project documents, decisions, assets, extracted text, and RAG
  index material
- is the first source for project facts
- can contain project-specific exceptions to global methods where allowed

KeyMemory:

- stores relay summaries, handoff notes, preferences, and semantic pointers
- helps agents continue work across sessions, agents, and subprojects
- is not the source of truth for project facts

Fact authority:

1. Project knowledge base
2. Company global knowledge base
3. Licensed industry reference layer
4. KeyMemory

Handoff authority:

1. Current task state
2. KeyMemory project relay
3. Latest project decisions
4. Company global methods

Licensed industry reference layer:

- contains provider-sold or provider-licensed online industry knowledge
- is mounted by entitlement, not copied into tenant source storage
- can be scoped to the whole company, one project, or selected specialist Agents
- returns authorized snippets, citations, and source ids only
- forbids download, export, bulk copy, direct filesystem access, or use outside
  Digital Office

Online knowledge injection rule:

- customer-owned external knowledge can be synced into company knowledge, project
  knowledge, or specialist Agent context according to admin settings
- provider-sold industry knowledge must be mounted as licensed reference, never
  as readable company/project source files
- department-specific knowledge spaces may scope company/project/legal or other
  domain materials to the department and its specialist Agents, but project
  source files remain the authority for active project facts

## Rules

Rule priority:

1. system bootstrap rules
2. company global rules
3. project rules
4. agent rules
5. task instructions

Rules are file-backed under `agent-system/rules/` so the GUI can create,
review, activate, and version them without editing Hermes core code.

## Multimodal Knowledge

Uploaded files are stored locally. Extracted text and metadata become the
searchable knowledge representation.

Default processing is local-first:

- text and markdown: local parsing
- Word: local DOCX extraction
- PDF: `pdftotext` or `pypdf`
- image OCR: Tesseract or RapidOCR after deployment
- optional enhanced OCR: PaddleOCR after deployment
- RAG embeddings: local sentence-transformer models after deployment

Vision LLM fallback is reserved for cases where local OCR is low-confidence or
where visual understanding is needed beyond text extraction.

No model weights are committed to the release repository. They are installed on
the enterprise host by `agent-system/bin/install-local-models`.

## Data Sharing

The product can offer friendly, transparent settings such as "Help improve the
experience" and "Industry experience co-building".

Allowed by default:

- route and workflow telemetry without raw prompts
- health and capability status
- approved methodology summaries
- anonymized relay patterns

Forbidden by default:

- raw company/project documents
- raw images
- unapproved drafts
- raw KeyMemory records
- credentials and secrets

Admins must be able to review exports and turn sharing off.

## Release Model

Production customers should receive provider-validated Digital Office releases,
not direct upstream Hermes or skill updates.

A release can include:

- Hermes runtime
- `agent-system`
- profile templates
- skill bundles
- GUI build
- local model installers
- migration and rollback metadata

The customer-facing button should be "Check for product updates". The backend
stages signed packages, backs up the current deployment, installs atomically,
runs post-install health checks, and supports rollback.
