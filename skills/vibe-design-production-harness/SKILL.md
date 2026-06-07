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

## Skeuomorphic Digital Office Notes

- Use physical-office metaphors only when they improve comprehension or emotional presence.
- Do not let metaphor reduce efficiency; operational tools still need dense, scannable information.
- Treat surfaces, folders, desks, documents, and rooms as interaction language, not decoration.
- Every visual metaphor must map to a user action, project state, Agent state, or knowledge object.

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
