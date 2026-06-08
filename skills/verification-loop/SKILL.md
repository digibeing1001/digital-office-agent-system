---
name: verification-loop
description: Comprehensive verification system for production-ready code. Build -> Type Check -> Lint -> Test -> Security -> Diff Review. Use after completing a feature, before creating a PR, or when ensuring quality gates pass.
origin: digital-office
---

# Verification Loop

A comprehensive verification system for production-ready code.

## When to Use

Invoke this skill:
- After completing a feature or significant code change
- Before creating a PR
- When you want to ensure quality gates pass
- After refactoring

## Verification Phases

### Phase 1: Build Verification

```bash
# Check if project builds
npm run build 2>&1 | tail -20
# OR
pnpm build 2>&1 | tail -20
# OR
python3 -m py_compile agent-system/bin/office-system.py 2>&1
```

If build fails, STOP and fix before continuing.

### Phase 2: Type Check

```bash
# TypeScript projects
npx tsc --noEmit 2>&1 | head -30

# Python projects
pyright . 2>&1 | head -30
# OR
mypy . 2>&1 | head -30
```

Report all type errors. Fix critical ones before continuing.

### Phase 3: Lint Check

```bash
# JavaScript/TypeScript
npm run lint 2>&1 | head -30

# Python
ruff check . 2>&1 | head -30
# OR
flake8 . 2>&1 | head -30
```

### Phase 4: Test Suite

```bash
# Run tests with coverage
npm run test -- --coverage 2>&1 | tail -50

# Python
pytest --cov=. --cov-report=term-missing 2>&1 | tail -30
```

Report:
- Total tests: X
- Passed: X
- Failed: X
- Coverage: X%

Target: 80% minimum coverage.

### Phase 5: Security Scan

```bash
# Check for secrets
grep -rn "sk-" --include="*.ts" --include="*.js" --include="*.py" . 2>/dev/null | head -10
grep -rn "api_key\|apikey\|api-key\|password\|secret" --include="*.ts" --include="*.js" --include="*.py" . 2>/dev/null | head -10

# Check for console.log in production code
grep -rn "console.log" --include="*.ts" --include="*.tsx" src/ 2>/dev/null | head -10

# Check for debug flags
# Python: remove pdb, ipdb, print-debug statements
grep -rn "import pdb\|import ipdb\|breakpoint()" --include="*.py" . 2>/dev/null | head -10
```

### Phase 6: Diff Review

```bash
# Show what changed
git diff --stat
git diff HEAD~1 --name-only
```

Review each changed file for:
- Unintended changes
- Missing error handling
- Potential edge cases
- Scope creep (changes not related to the stated goal)

## Output Format

After running all phases, produce a verification report:

```
VERIFICATION REPORT
==================

Build:     [PASS/FAIL]
Types:     [PASS/FAIL] (X errors)
Lint:      [PASS/FAIL] (X warnings)
Tests:     [PASS/FAIL] (X/Y passed, Z% coverage)
Security:  [PASS/FAIL] (X issues)
Diff:      [X files changed]

Overall:   [READY/NOT READY] for PR

Issues to Fix:
1. ...
2. ...
```

## Continuous Mode

For long sessions, run verification every 15 minutes or after major changes:

```markdown
Set a mental checkpoint:
- After completing each function
- After finishing a component
- Before moving to next task
```

## Integration with AI Native Loop

This verification loop maps to the Digital Office AI Native Loop:

- **Perceive** — Understand what was built and what gates apply.
- **Plan** — Determine which verification phases are relevant for this change.
- **Execute** — Run the verification phases in order.
- **Reflect** — Review results, identify gaps, assess readiness.
- **Iterate** — If issues found, propose fixes as user-visible iteration proposals.

## Gate Mapping

| Verification Phase | Corresponding Harness Gate |
|-------------------|---------------------------|
| Build Verification | `build_or_compile_passes` |
| Type Check | `type_check_passes` |
| Lint Check | `lint_passes` |
| Test Suite | `deterministic_tests_pass` |
| Security Scan | `secret_scan_has_no_hits` |
| Diff Review | `git_diff_is_reviewable` |
