---
name: vibe-coding-production-harness
description: Production-grade harness for vibe coding work: scope, implementation, deterministic tests, review, rollback, and delivery artifacts.
origin: digital-office
---

# Vibe Coding Production Harness

Use this skill whenever the `implementation` role is asked to produce, modify, review, or ship code.

## Operating Principle

Good vibe coding is not improvisation. It is fast creative implementation inside a visible harness:

1. Understand the requested behavior.
2. Identify the smallest safe change.
3. Implement with local conventions.
4. Prove the change with deterministic checks.
5. Report exactly what changed and what remains risky.

## Entry Contract

Before editing code, confirm:

- The product/design intent is clear enough to test.
- The likely files or modules are identified.
- Acceptance criteria can be judged by commands, snapshots, smoke flows, or explicit review checks.
- The change does not require hidden production update, data access, or credential work.

If any item is missing, return to secretary or product/design role for clarification.

## Execution Loop

1. Inspect local patterns before editing.
2. Keep edits narrowly scoped.
3. Prefer deterministic tests over self-review.
4. For frontend work, include visual and responsive verification when a runnable UI exists.
5. For backend/CLI work, include compile, JSON/schema, command, and smoke checks.
6. Record failed checks and the fix applied.
7. Stop when all required gates pass or when a clear blocker is found.

## Required Gates

- `build_or_compile_passes`
- `deterministic_tests_pass`
- `smoke_tests_pass`
- `secret_scan_has_no_hits`
- `git_diff_is_reviewable`
- `no_unapproved_scope_expansion`

## Output Contract

Return:

- files changed
- behavior changed
- commands run
- pass/fail status
- unresolved risks
- rollback note

Do not claim production readiness unless the required gates passed.

## Review Heuristics

- User-facing behavior must match the product/design acceptance criteria.
- Tests should catch the bug or drift that would matter to the user.
- Avoid large refactors unless they remove a real instability.
- Do not add broad dependencies unless the product benefit is clear and testable.
- If the same model wrote the code, use deterministic checks before trusting review language.
