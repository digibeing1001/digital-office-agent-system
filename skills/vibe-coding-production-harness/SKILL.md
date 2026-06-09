---
name: vibe-coding-production-harness
description: Production-grade harness for vibe coding work: scope, implementation, deterministic tests, review, rollback, and delivery artifacts.
origin: digital-office
---

# Vibe Coding Production Harness

Use this skill whenever the `implementation` role is asked to produce, modify, review, or ship code.

## Soul Principles (inherited from Karpathy)

These four principles sit above every phase below. When a phase rule conflicts with a soul principle, the soul principle wins.

1. **Think Before Coding** — State assumptions. Surface tradeoffs. Ask when uncertain. Never silently pick between competing interpretations.
2. **Simplicity First** — Minimum code that solves the problem. No speculative features. No abstractions for single-use code. No error handling for impossible scenarios. If 200 lines could be 50, rewrite.
3. **Surgical Changes** — Touch only what the request demands. Do not "improve" adjacent code, comments, or formatting. Match existing style. Remove only YOUR orphans. Every changed line must trace to the user's request.
4. **Goal-Driven Execution** — Transform tasks into verifiable goals with concrete pass/fail signals ("Add validation" → "Write tests for invalid inputs, then make them pass"). State a brief plan with verify steps for multi-step work.

These principles also live in each Coder Agent's SOUL.md (`kenny-vibe-coder` personal + `office-coder` product). When invoking this harness, treat the four principles as binding unless an explicit user override is given.

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

---

# AI Native Eight-Phase Decision Tree

This harness operates inside an eight-phase loop. **Pick the smallest path that matches the task**. Small tasks skip the heavyweight phases; complex tasks route through every one.

```
User says "build X"
    │
    ▼
≤ 15 min change? ──→ fast-path: intent → diff → smoke → done
    │
    └─→ > 15 min
            │
            UI work? ──→ include Phase 3 Design (score ≥ 7.5)
            │
            new project? ──→ Phase 1 + Phase 2 with product/design routing
            │
            existing project? ──→ Phase 1 baseline + Phase 2 minimum plan
            │
            ▼
        1. Perceive  →  2. Plan  →  3. Design (UI)  →  4. Execute
            →  5. Verify  →  6. Review  →  7. Ship  →  8. Reflect
```

### Phase Routing Table

| Trigger | Phase | Skill to Invoke |
|---------|-------|-----------------|
| "Build X", "Add feature", "Fix bug" | 1 → 4 → 5 | `vibe-coding-production-harness` (this skill) |
| "Design UI", "Make it pretty" | 3 → 4 | `vibe-design-production-harness` |
| "Review code", "Audit" | 6 | `verification-loop` + six-role review checklist (below) |
| "Debug this", "Why is it slow" | 4 (debug branch) | `systematic-debugging` |
| "Refactor X" | 4 → 5 → 6 | `coding-standards` + `verification-loop` |
| "Ship", "Deploy", "Release" | 5 → 6 → 7 | `verification-loop` → six-role review → production gate |
| "Plan X", "Break down epic" | 2 | `brainstorming` → `grill-me` for depth |
| "Generate tests" | 5 | `test-driven-development` + `verification-loop` |
| "Setup CI" / "Add hooks" | 7 | `finishing-a-development-branch` |
| "Hand off", "Pause", "Resume" | 8 | `handoff` + KeyMemory relay |

**Rule**: Process skill > Implementation skill. When in doubt, route to `vibe-coding-production-harness` first; it will branch into the right sub-skill.

---

# Quality Gates (Quantified)

## Code Quality Gate

| Dimension | Pass Criteria | Verification |
|-----------|--------------|--------------|
| **Type Safety** | `tsc --noEmit` zero errors | CLI |
| **Lint** | ESLint + Prettier zero errors | CLI |
| **Test Coverage** | Smoke Test ≥ 3 assertions per module | Test runner |
| **Dead Code** | No unused imports/vars/functions (`no-unused`) | Static analysis |
| **Cyclomatic Complexity** | Single function ≤ 15 | Static analysis |
| **File Length** | Single file ≤ 400 lines (split if exceeded) | Manual |

**Hard rule**: 3+ test failures = module needs redesign, not patch-and-pray.

## Design Quality Gate (UI Projects Only)

| Dimension | Weight | Pass Criteria | Verification |
|-----------|--------|--------------|--------------|
| Visual Distinctiveness | 20% | Non-default font, no purple-gradient-on-white, clear palette | Visual review |
| Usability | 25% | Krug's law: self-evident, painless click, scannable copy | Heuristic |
| Accessibility | 20% | WCAG 2.2 AA: 4.5:1 body, 3:1 UI, semantic HTML, keyboard | axe-core / manual |
| Technical Quality | 15% | Image dimensions, lazy-load, no `transition: all`, 60fps | Lighthouse |
| Motion | 10% | Only `transform`/`opacity`, respects `prefers-reduced-motion`, interruptible | DevTools |
| Copy | 10% | Active voice, specific button labels, errors include next step | Manual |
| **Total** | 100% | **≥ 7.5 / 10** required to ship | Self-score |

If score < 7.5, return to Phase 3 with the gap list. Do not ship UI below the gate.

## Security Gate

- No hardcoded secrets, passwords, tokens (regex scan + grep)
- All user input validated + escaped
- Parameterized SQL (no string concatenation)
- No `eval()` / `new Function()` on user input
- OWASP Top 10 self-audit: no high/critical findings
- Dependencies: `npm audit --audit-level=moderate` clean

## Ship Gate (must all pass)

| Gate | Trigger | Required |
|------|---------|----------|
| Lint | on save | ✓ |
| Smoke Test | per module | ≥ 3 assertions, all green |
| Design Score | design complete | ≥ 7.5 / 10 |
| Code Review | feature complete | no blocking findings |
| Security | pre-ship | no high/critical |
| Browser QA | pre-ship (UI) | no regressions |

---

# Six-Role Review Checklist

When code is ready to ship, run reviews from six distinct role lenses. Each role produces a separate findings list. Do not collapse roles — they catch different classes of problem.

| Role | Question | Output Format |
|------|----------|---------------|
| **CEO** | Does this match business goal? Is scope creeping? | "In/out of scope: ..."; "Wasted work: ..." |
| **Architect** | Is structure sound? Will it create tech debt? | "Boundaries: ..."; "Debt introduced: ..."; "Refactor needed: yes/no" |
| **DevEx** | Can a new dev onboard this in < 1 day? | "Onboarding blockers: ..."; "Naming consistency: ..." |
| **QA** | Edge cases? Error paths? Flaky tests? | "Untested paths: ..."; "Flakiness risk: ..."; "Coverage gaps: ..." |
| **Security** | OWASP Top 10? STRIDE? Hardcoded secrets? | "Threats: ..."; "Severity: critical/high/medium/low"; "Fix: ..." |
| **Designer** | Visual consistency? AI slop? Accessibility? | "Slop score: ..."; "Consistency: ..."; "a11y: ..." |

**Output template** for each review pass:

```
## Role: <name>
L<file>:<line> <severity> <problem>. <fix>.
...
**Verdict**: ship / rework / block
```

**Verdict aggregation**:
- Any `block` → return to Phase 4 with rework list
- Any `critical` Security finding → block until fixed
- 3+ `medium` findings → rework recommended
- Otherwise → ship

---

# Hooks Mapping (Hermes Adaptation)

The source `claude-vibe-coding-setup` uses Claude Code's `hooks.json` for automated gates. Under Hermes, those hooks map to **skill invocations at phase boundaries**:

| Source Hook | Hermes Equivalent |
|-------------|-------------------|
| `pre-commit` (prettier/eslint/tsc) | Phase 4 self-check before commit message |
| `pre-test` (vitest/playwright) | Phase 5 `verification-loop` |
| `pre-ship` (security-review/qa/code-review) | Phase 6 six-role review + Phase 7 ship gate |
| `pre-merge` (simplify/caveman-review) | Phase 6 `simplify` + manual lint |

**Rationale**: Hermes has no file-watcher hook infrastructure. The Coder Agent must invoke the corresponding skill at the right phase boundary. This is enforced by SOUL.md and `agents.registry.json` `default_skill_chain`.

---

# Toolkit Plugin Mapping (Avoid Pollution)

The source bundle ships 120+ Claude Code plugins. Under Hermes, we **do not** install them one-to-one. Instead:

| Source Plugin | Hermes Native Equivalent |
|---------------|--------------------------|
| `code-architect` | `improve-codebase-architecture` skill |
| `schema-designer` | domain skill (project-specific) |
| `ui-designer` / `frontend-developer` | `vibe-design-production-harness` + `frontend-patterns` |
| `code-review-assistant` / `code-guardian` | six-role review checklist above + `plankton-code-quality` |
| `dead-code-finder` | `coding-standards` lint rules |
| `a11y-audit` | Design Quality Gate (a11y 20% weight) |
| `bundle-analyzer` | Lighthouse (run on demand) |
| `deploy-pilot` / `release-manager` | `finishing-a-development-branch` skill |
| `codebase-documenter` | Diataxis-style doc task in Phase 7 |
| `security-guidance` | Security Gate + role-based review |

When a project genuinely needs a plugin that has no Hermes equivalent, escalate via KeyMemory entity with the `tooling-gap` tag — do not silently install Claude Code plugins.

---

# Cross-Session Memory

The source uses Claude Mem for cross-session memory. Under Hermes, **KeyMemory is the only durable memory** (see `~/.hermes/SOUL.md` global rule #2). The Coder Agent:

1. Reads prior relay notes from KeyMemory before starting Phase 1 (Perceive).
2. Writes implementation summary, gates passed, and residual risks to KeyMemory at Phase 8 (Reflect).
3. Never writes durable facts to local `~/.hermes/MEMORY.md` or session-bound memory tools — those are session-scoped only.

If a decision affects future Coder Agent behavior (e.g., "always run axe-core on UI tasks"), promote it to KeyMemory `entity` layer and mirror to the relevant SOUL.md (rule #3 of global rules).
