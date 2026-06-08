# PPT Production Workflow

`ppt_production` turns a presentation request into a validated deck artifact without hiding responsibilities inside one role.

## Role Sequence

The workflow order is `intake -> writing -> design -> intake`.

1. `intake` (`secretary`) clarifies the audience, goal, source material, constraints, acceptance criteria, output format, and delivery expectations.
2. `writing` (`writer`) produces the storyline, slide-by-slide copy, and speaker notes or narration guidance.
3. `design` (`vibe-designer`) produces the visual direction, layout system, media decisions, and renderable deck artifact.
4. `intake` (`secretary`) runs gate checks, records assumptions and risks, and gives the user the artifact path, URL, or open instructions.

## Boundaries

- Writer does not own final HTML/PPT rendering unless a deck-rendering skill is explicitly registered for the Writer.
- Designer owns the visual direction, layout system, media decisions, and renderable deck artifact because the PPT rendering skills are registered on the design path.
- Secretary owns the final gate: intake, route selection, final validation, and delivery notes.
- External deck skills remain staged product capabilities and must be tracked in `skills.sources.json`.

## Validation

The workflow is covered by route tests in `agent-system/agents.registry.json` using the router-supported fields:

- `expect`
- `expect_workflow`
- `expect_steps`

`agent-system/bin/harness-check` must pass before this workflow is treated as ready for product sync or release.
