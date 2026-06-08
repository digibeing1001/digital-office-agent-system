---
name: vibe-design-production-harness
description: Production-grade harness for vibe design work: product intent, interaction states, visual QA, accessibility, and implementation handoff.
origin: digital-office
---

# Vibe Design Production Harness

Use this skill whenever the `design` role creates or reviews GUI, UX, visual direction, prototype behavior, or implementation handoff.

## Operating Principle

Good vibe design is expressive but still operational. The design Agent must preserve taste, usability, and implementation clarity.

## Entry Contract

Before designing, confirm:

- target user and job-to-be-done
- primary workflow and success state
- target device and viewport assumptions
- existing product style or desired visual direction
- constraints from implementation, accessibility, or enterprise deployment

If the product intent is unclear, route through the `product` role before design.

## Design Gates

- `primary_states_specified`: default, loading, empty, error, disabled, success, and handoff states are covered when relevant.
- `responsive_behavior_specified`: desktop and mobile behavior are defined.
- `text_overflow_checked`: labels, buttons, cards, and panels cannot break layout.
- `accessibility_checked`: contrast, focus path, keyboard path, and hit targets are considered.
- `visual_quality_checked`: composition is not generic, one-note, cluttered, or decorative without purpose.
- `implementation_handoff_ready`: design decisions are specific enough for the implementation Agent.

## AI Native Loop Placement

Design work lives inside the Digital Office loop:

- Perceive: read product intent, user type, project context, rules, knowledge objects, and prior relay notes.
- Plan: define interaction states, responsive behavior, accessibility checks, and implementation handoff before drawing conclusions.
- Execute: produce the design spec or prototype artifact.
- Reflect: review the design against workflow clarity, visual quality, accessibility, and implementation readiness.
- Iterate: propose improvements only as a user-visible iteration proposal. Do not silently rewrite product rules, workflows, Agent behavior, or skill bundles.

## Frontend Patterns Integration

When designing for React/Next.js implementations:

- Use composition patterns (compound components, render props) over inheritance.
- Design for state management patterns (Context + Reducer, Zustand) from the start.
- Consider performance implications (memoization, lazy loading, virtualization) in the design spec.
- Specify error boundary behavior for each major component area.
- Define form validation patterns (Zod schemas) for all user input.

For detailed frontend patterns, invoke `frontend-patterns` skill.

## Skeuomorphic Digital Office Notes

- Use physical-office metaphors only when they improve comprehension or emotional presence.
- Do not let metaphor reduce efficiency; operational tools still need dense, scannable information.
- Treat surfaces, folders, desks, documents, and rooms as interaction language, not decoration.
- Every visual metaphor must map to a user action, project state, Agent state, or knowledge object.

## External Visual Direction Tool: huashu-design

When the design task needs a parallel comparison of visual directions or a structured expert review, the design Agent MAY delegate to the `huashu-design` skill. This is an optional accelerator, not a replacement for the harness's own gate checks.

Use huashu-design when:

- the user asks for design direction, style comparison, or "which visual feels right" decisions
- the task is a presentation or pitch deck that needs parallel visual concepts
- the user requests a structured expert review on a design artifact

Do not use huashu-design when:

- the task is only a single visual decision the Agent can justify directly
- the design must conform to a pre-existing design system or brand contract
- the user asks for a deterministic, gate-driven design check rather than style exploration

The harness gates above (`primary_states_specified`, `responsive_behavior_specified`, `text_overflow_checked`, `accessibility_checked`, `visual_quality_checked`, `implementation_handoff_ready`) remain authoritative. huashu-design outputs are advisory inputs that the Agent must still validate against these gates before handoff.

## Presentation Deck Ownership

For `ppt_production`, the Writer owns storyline, slide copy, and speaker notes. The Designer owns visual direction, page composition, media decisions, and the renderable deck artifact. Do not move final deck rendering to Writer unless the Writer has an explicitly registered deck-rendering skill and the workflow has been updated through the normal validation path.

## Output Contract

Return:

- product intent restatement
- interaction flow
- state list
- layout and responsive rules
- visual direction
- accessibility notes
- implementation handoff
- risks to verify in browser or prototype

Do not hand off to implementation until the minimum design gates pass.

## Sub-Skills

| Skill | When to Invoke |
|-------|---------------|
| `frontend-patterns` | React/Next.js design work |
| `coding-standards` | Design system token definitions |
| `verification-loop` | Pre-handoff quality check |
