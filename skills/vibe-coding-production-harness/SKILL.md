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

## AI Native Loop Placement

Implementation work lives inside the Digital Office loop:

- Perceive: read the current task, project context, product/design handoff, relevant knowledge entries, and prior relay notes.
- Plan: name files, acceptance checks, risk, and rollback before editing.
- Execute: produce the diff and run deterministic checks.
- Reflect: report failed checks, unresolved risk, and whether the implementation matched the handoff.
- Iterate: propose improvements only as a user-visible iteration proposal. Do not silently change rules, workflows, Agent behavior, or skill bundles.

## TDD Discipline

When tests are applicable, follow vertical slicing (tracer bullets):

```
WRONG (horizontal slicing):
  RED:   test1, test2, test3, test4, test5
  GREEN: impl1, impl2, impl3, impl4, impl5

RIGHT (vertical / tracer bullets):
  RED->GREEN: test1->impl1
  RED->GREEN: test2->impl2
  RED->GREEN: test3->impl3
  ...
```

- One test at a time. Only enough code to pass the current test.
- Tests describe behavior through public interfaces, not implementation details.
- Good tests read like specifications and survive refactors.
- Never refactor while RED. Get to GREEN first.

## Systematic Debugging Integration

When a bug is encountered during implementation:

1. **Build a feedback loop** — Create a fast, deterministic pass/fail signal.
2. **Reproduce** — Confirm the loop produces the user's described failure.
3. **Hypothesise** — Generate 3-5 ranked, falsifiable hypotheses.
4. **Instrument** — Map each probe to a specific prediction. One variable at a time.
5. **Fix + regression test** — Write regression test before fix (if correct seam exists).
6. **Cleanup** — Remove instrumentation, verify original repro no longer reproduces.

For detailed debugging methodology, invoke `systematic-debugging` skill.

## Verification Loop

After implementation, run the verification sequence:

1. **Build/Compile** — Ensure the project builds without errors.
2. **Type Check** — Run type checker (tsc, pyright, etc.).
3. **Lint** — Run linter (eslint, ruff, etc.).
4. **Tests** — Run test suite with coverage target (80%+).
5. **Security Scan** — Check for secrets, console.log, unsafe patterns.
6. **Diff Review** — Review each changed file for unintended changes.

For detailed verification methodology, invoke `verification-loop` skill.

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

## Sub-Skills

| Skill | When to Invoke |
|-------|---------------|
| `coding-standards` | Starting new module, reviewing code quality |
| `systematic-debugging` | Hard bugs, performance regressions |
| `verification-loop` | Pre-PR verification, comprehensive quality check |
| `frontend-patterns` | React/Next.js component work |
