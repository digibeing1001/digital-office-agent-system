---
name: digital-lawyer-workflows
description: Enterprise digital lawyer workflow pack for Digital Office. Maps legal source packs into controlled legal intake, contract review, compliance review, source verification, and human approval gates.
---

# Digital Lawyer Workflows

Use this skill when a Digital Office workflow enters the enterprise digital lawyer capability. The digital lawyer is one product-visible digital employee. Contract review, compliance review, privacy review, dispute triage, and legal synthesis are internal skill lanes, not separate subordinate Agents.

## Core Rules

- Treat every legal output as an internal review draft for human professional review.
- Do not provide final legal opinions, legal conclusions, filing advice, or external communications without explicit human approval.
- Cite project files, company rules, licensed reference ids, or connector results. If authority is not verified, mark it as unverified.
- Use the smallest workflow lane that can satisfy the task. Do not invent extra digital employees or simulate a human legal hierarchy.
- Keep customer documents inside project/company knowledge spaces. Do not copy raw documents into source skills, public repositories, or provider-owned catalog assets.
- Every handoff must use the context envelope fields required by `agent-system/context-envelope.schema.json`.

## Source Packs

### claude-for-legal-zh

Source: `https://github.com/cslawyer1985/claude-for-legal-zh`

Status: installed local source pack for the digital lawyer, Apache 2.0. The local copy lives at `skills/_imported/claude-for-legal-ZH` and is verified by `agent-system/bin/install-skill-sources`. Use through this workflow wrapper and the normal verification and approval flow.

Useful lanes:

- `commercial-legal`: vendor agreement review, NDA triage, SaaS agreement review, amendment history, escalation flagging.
- `corporate-legal`: diligence tables, issue extraction, written consents, material contract schedules, entity compliance.
- `privacy-legal`: PIA, DPA review, DSAR response, privacy use-case triage, policy monitoring.
- `product-legal`: launch review, marketing claims review, feature risk assessment.
- `employment-legal`: termination review, hiring review, worker classification, policy drafting.
- `ip-legal`: IP clause review, open-source compliance, takedown triage, portfolio checks.
- `regulatory-legal`: policy diff, regulatory feed watching, comments, gap tracking.
- `ai-governance-legal`: AI use-case triage, vendor AI review, AI policy gap analysis.
- `litigation-legal`: demand-letter intake, dispute triage, matter briefing, evidence review, outside-counsel status.

### Legal-Skills-Chinese

Source: `https://github.com/THUYRan/Legal-Skills-Chinese`

Status: reference-only until licensing is cleared. The repository states CC BY-NC-ND 4.0 terms, so do not vendor, modify, redistribute, or use it commercially without approval.

Useful reasoning patterns to map after clearance:

- Retrieval and validity: `legal-article-retrieval`, `case-retrieval`, `other-legal-retrieval`, `legal-norm-validity-check`.
- Fact and element work: `legal-element-extraction`, `structured-element-extraction`, `dispute-issue-identification`, `evidence-evaluation`.
- Interpretation and reasoning: `legal-interpretation-argument`, `systematic-interpretation`, `teleological-interpretation`, `deductive-reasoning`, `analogical-reasoning`, `conflict-resolution`.
- Risk and prioritization: `legal-risk-assessment`, `internal-compliance-risk-identification`, `strategic-risk-prioritization`, `dispute-and-performance-risk`.
- Documents: `legal-document-summarization`, `multi-document-summarization`, `legal-document-formatting`, `legal-terminology`.

## Workflows

### legal_triage

Use when the user asks the digital lawyer for help but the legal lane is unclear.

Output:

- matter type
- jurisdiction and governing-law assumptions
- source materials required
- suggested workflow
- human review requirement

### legal_contract_review

Use for supplier, customer, SaaS, NDA, procurement, services, partnership, amendment, and contract dispute questions.

Recommended source mapping:

- `commercial-legal:review`
- `commercial-legal:amendment-history`
- `commercial-legal:escalation-flagger`
- `corporate-legal:material-contract-schedule`
- after clearance: element extraction, norm validity, dispute/performance risk, legal risk assessment

Output:

- contract metadata and version
- clause risk matrix
- issue list by severity
- proposed fallback positions
- unresolved assumptions
- human approval gates

### legal_privacy_data_review

Use for personal information, privacy, data processing, DPA, PIA, DSAR, cross-border transfer, and data-rights matters.

Recommended source mapping:

- `privacy-legal:use-case-triage`
- `privacy-legal:pia-generation`
- `privacy-legal:dpa-review`
- `privacy-legal:dsar-response`
- `privacy-legal:reg-gap-analysis`
- after clearance: norm validity, internal compliance risk, strategic risk prioritization

Output:

- data-role and data-flow assumptions
- risk and control matrix
- required notices, consents, assessments, or agreements
- blocked actions
- human approval gates

### legal_product_compliance_review

Use for product launch, marketing claims, AI governance, regulatory change, and compliance readiness.

Recommended source mapping:

- `product-legal:launch-review`
- `product-legal:marketing-claims-review`
- `product-legal:feature-risk-assessment`
- `ai-governance-legal:use-case-triage`
- `ai-governance-legal:vendor-ai-review`
- `regulatory-legal:policy-diff`
- `regulatory-legal:gaps`

Output:

- launch/compliance decision draft
- risk register
- mitigation actions
- owners and deadlines
- human approval gates

### legal_employment_ip_review

Use for employment, hiring, termination, worker classification, internal investigation, IP clause, open-source, trademark, copyright, or patent triage.

Recommended source mapping:

- `employment-legal:termination-review`
- `employment-legal:hiring-review`
- `employment-legal:worker-classification`
- `employment-legal:policy-drafting`
- `ip-legal:ip-clause-review`
- `ip-legal:oss-review`
- `ip-legal:clearance`
- `ip-legal:fto-triage`

Output:

- issue classification
- required evidence and stakeholder inputs
- risk and action matrix
- external counsel trigger, if needed
- human approval gates

### legal_dispute_triage

Use for demand letters, received lawyer letters, disputes, litigation/arbitration readiness, evidence review, and outside-counsel coordination.

Recommended source mapping:

- `litigation-legal:demand-intake`
- `litigation-legal:demand-received`
- `litigation-legal:matter-briefing`
- `litigation-legal:privilege-log-review`
- `litigation-legal:oc-status`
- after clearance: evidence evaluation, dispute issue identification, argument chain construction, strategic risk prioritization

Output:

- posture and deadline summary
- facts and evidence gap list
- response options
- escalation path
- external counsel package checklist

## Final Gate

Before delivery, the digital lawyer must produce:

1. business-facing summary
2. source and verification status
3. risk levels and recommended next steps
4. blocked actions
5. explicit human review requirements
