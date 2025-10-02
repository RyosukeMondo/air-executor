# Sample JavaScript/TypeScript Project

Small test project for multi-language orchestrator testing.

## Intentional Issues

### P1: Static Analysis
- ❌ **Unused import**: `path` in calculator.ts
- ❌ **Missing return type**: `multiply()` function
- ❌ **High complexity**: `complexCalculator()` has complexity > 10
- ❌ **File size**: `largeModule.ts` exceeds 500 lines

### P2: Tests
- ✅ **Passing**: 9 tests pass
- ❌ **Failing**: 2 tests fail intentionally
  - `divide` - wrong assertion (expects 3 instead of 2.5)
  - `complexCalculator power` - wrong expected value (expects 6 instead of 8)

### P3: Coverage
- ❌ **No coverage**: `advancedMath()` - never tested
- ❌ **No coverage**: `handleEdgeCases()` - never tested
- ❌ **Partial coverage**: `complexCalculator()` - only 3/11 operations tested

## Setup

```bash
# Install dependencies
npm install

# Or with yarn
yarn install
```

## Running Tests

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run linter
npm run lint

# Type check
npm run typecheck
```

## Expected Results

### P1 Static Analysis
- ESLint errors: 2-3 (unused import, missing return type)
- TypeScript errors: 1-2 (type issues)
- Complexity violations: 1 (complexCalculator)
- File size violations: 1 (largeModule.ts)
- **Score: ~60-70%** (intentionally below 90% threshold)

### P2 Tests
- Total: 11 tests
- Passing: 9
- Failing: 2
- **Score: 82%** (intentionally below 85% threshold)

### P3 Coverage
- Overall: ~45-55%
- Gaps: 2 functions with no coverage
- **Needs**: Tests for advancedMath(), handleEdgeCases()
