# Planner Agent Rule Overlay

The planner must base planning work on research facts. For planning tasks,
prefer the `research_then_plan` workflow from `agents.registry.json`.

Do not invoke researcher through `delegate_task`; use the router or the
workflow execution contract.
