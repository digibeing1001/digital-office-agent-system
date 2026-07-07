---
name: coding-standards
description: Baseline cross-project coding conventions for naming, readability, immutability, error handling, and code-quality review. Use with frontend-patterns or backend-patterns for framework-specific guidance.
origin: digital-office
---

# Coding Standards & Best Practices

Baseline coding conventions applicable across projects. This skill is the shared floor, not the detailed framework playbook.

## When to Activate

- Starting a new project or module
- Reviewing code for quality and maintainability
- Refactoring existing code to follow conventions
- Enforcing naming, formatting, or structural consistency

## Scope Boundaries

Activate this skill for:
- Descriptive naming
- Immutability defaults
- Readability, KISS, DRY, and YAGNI enforcement
- Error-handling expectations and code-smell review

Do not use this skill as the primary source for:
- React composition, hooks, or rendering patterns (use frontend-patterns)
- Backend architecture, API design, or database layering (use backend-patterns)

## Code Quality Principles

### 1. Readability First
- Code is read more than written
- Clear variable and function names
- Self-documenting code preferred over comments
- Consistent formatting

### 2. KISS (Keep It Simple, Stupid)
- Simplest solution that works
- Avoid over-engineering
- No premature optimization
- Easy to understand > clever code

### 3. DRY (Don't Repeat Yourself)
- Extract common logic into functions
- Create reusable components
- Share utilities across modules
- Avoid copy-paste programming

### 4. YAGNI (You Aren't Gonna Need It)
- Don't build features before they're needed
- Avoid speculative generality
- Add complexity only when required
- Start simple, refactor when needed

## Naming Conventions

### Variables
```typescript
// PASS: Descriptive names
const marketSearchQuery = 'election'
const isUserAuthenticated = true
const totalRevenue = 1000

// FAIL: Unclear names
const q = 'election'
const flag = true
const x = 1000
```

### Functions
```typescript
// PASS: Verb-noun pattern
async function fetchMarketData(marketId: string) { }
function calculateSimilarity(a: number[], b: number[]) { }
function isValidEmail(email: string): boolean { }

// FAIL: Unclear or noun-only
async function market(id: string) { }
function similarity(a, b) { }
function email(e) { }
```

## Immutability Pattern (CRITICAL)

```typescript
// PASS: ALWAYS use spread operator
const updatedUser = { ...user, name: 'New Name' }
const updatedArray = [...items, newItem]

// FAIL: NEVER mutate directly
user.name = 'New Name'  // BAD
items.push(newItem)     // BAD
```

## Error Handling

```typescript
// PASS: Comprehensive error handling
async function fetchData(url: string) {
  try {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    return await response.json()
  } catch (error) {
    console.error('Fetch failed:', error)
    throw new Error('Failed to fetch data')
  }
}

// FAIL: No error handling
async function fetchData(url) {
  const response = await fetch(url)
  return response.json()
}
```

## Async/Await Best Practices

```typescript
// PASS: Parallel execution when possible
const [users, markets, stats] = await Promise.all([
  fetchUsers(), fetchMarkets(), fetchStats()
])

// FAIL: Sequential when unnecessary
const users = await fetchUsers()
const markets = await fetchMarkets()
const stats = await fetchStats()
```

## Type Safety

```typescript
// PASS: Proper types
interface Market {
  id: string
  name: string
  status: 'active' | 'resolved' | 'closed'
}

function getMarket(id: string): Promise<Market> {
  // Implementation
}

// FAIL: Using 'any'
function getMarket(id: any): Promise<any> {
  // Implementation
}
```

## Comments & Documentation

### When to Comment
```typescript
// PASS: Explain WHY, not WHAT
// Use exponential backoff to avoid overwhelming the API during outages
const delay = Math.min(1000 * Math.pow(2, retryCount), 30000)

// FAIL: Stating the obvious
// Increment counter by 1
count++
```

## Code Smell Detection

Watch for these anti-patterns:

1. **Long Functions** — Function > 50 lines without clear sub-task separation
2. **Deep Nesting** — More than 3 levels of indentation
3. **Magic Numbers** — Hardcoded values without named constants
4. **Feature Envy** — Method that uses more features of another class than its own
5. **Shotgun Surgery** — One change requires edits in many places
