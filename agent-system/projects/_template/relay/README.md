# Project Relay Memory

This folder is the file-backed audit queue for KeyMemory project relay entries.

Use relay memory for:

- cross-agent handoff
- subproject continuity
- latest project state snapshots
- unresolved blockers and next actions

Do not use relay memory as the authoritative source for active project facts.
Project source documents and approved project decisions still win.
