# Industry Knowledge And External Connectors

## Purpose

Digital Office needs two different knowledge channels:

1. customer-owned knowledge sources, such as ima, Notion, Tencent Docs, Get
   notes, AI recorder cards, Feishu Docs, and local company documents
2. provider-sold industry knowledge products, such as law references, tax policy
   references, accounting standards, curated papers, and industry methods

These channels must not share the same storage policy.

## Injection Targets

Customer-owned external knowledge can be injected into:

1. company knowledge base, when it is reusable across the organization
2. project knowledge base, when it belongs to one matter, case, client,
   campaign, or product build
3. specialist Agent context, when only a certain Agent should use it

Provider-sold industry knowledge must be injected as:

1. licensed company reference, when the tenant bought company-wide access
2. licensed project reference, when the pack is mounted to selected projects
3. licensed Agent reference, when only selected specialist Agents may retrieve it

Provider-sold industry knowledge must not be copied into company or project
knowledge source folders as readable files.

## Recommended Decision

Use this decision tree:

1. If the customer owns the content and wants all projects to reuse it, mount or
   sync it to company knowledge.
2. If the customer owns the content and it is tied to one project, mount or sync
   it to project knowledge.
3. If the customer owns the content but only one specialist Agent should use it,
   mount it as Agent specialist context.
4. If the content is sold or licensed by the provider, mount it as licensed
   industry reference.

## Licensed Knowledge Restrictions

Sold industry knowledge can be used only inside Digital Office.

Forbidden:

- download full pack
- export full pack
- bulk copy or sync to customer knowledge base
- direct source file path exposure
- external customer API access
- use outside Digital Office

Allowed:

- controlled retrieval inside the GUI
- Agent context injection inside the Digital Office runtime
- source id and citation display
- limited snippets under backend policy

## Identity And Audit

Every licensed industry knowledge request must include:

1. tenant id
2. deployment id
3. human user id and role
4. project id
5. Agent id
6. workflow run id
7. knowledge pack id
8. entitlement id
9. query hash
10. result source ids
11. allow or deny decision

The access log answers the business question: who used which paid knowledge
product, inside which enterprise deployment, for which project, through which
Agent, and under which entitlement.

## Connector Skill Model

Third-party knowledge products may bring their own skill. Digital Office should
not assume every source is a file import.

Each connector should declare:

- connector id
- source class
- provider
- auth type
- skill id
- sync modes
- mount targets
- permission mapping
- citation policy
- rate limit policy

The GUI should present these connectors as Knowledge Sources. The user should
not need to know whether the connector is implemented by Hermes, a skill, a
backend API, or an external OAuth integration.
