# Sample Go Project

Small test project for multi-language orchestrator testing.

## Intentional Issues

### P1: Static Analysis
- ❌ **Unused import**: `fmt` in calculator.go
- ❌ **High complexity**: `ComplexCalculator()` has complexity > 10
- ❌ **File size**: `large_module.go` exceeds 500 lines

### P2: Tests
- ✅ **Passing**: 6 tests pass
- ❌ **Failing**: 2 tests fail intentionally
  - `TestDivide` - wrong assertion (expects 3.0 instead of 2.5)
  - `TestComplexCalculatorPower` - wrong expected value (expects 6.0 instead of 8.0)

### P3: Coverage
- ❌ **No coverage**: `AdvancedMath()` - never tested
- ❌ **No coverage**: `HandleEdgeCases()` - never tested
- ❌ **Partial coverage**: `ComplexCalculator()` - only 3/11 operations tested

## Setup

```bash
# Download dependencies
go mod download

# Or with tidy
go mod tidy
```

## Running Tests

```bash
# Run all tests
go test ./...

# Run with verbose output
go test -v ./...

# Run with coverage
go test -cover ./...
go test -coverprofile=coverage.out ./...

# Run only short tests (P2 minimal strategy)
go test -short ./...
```

## Running Static Analysis

```bash
# Run go vet
go vet ./...

# Run staticcheck (if installed)
staticcheck ./...
```

## Expected Results

### P1 Static Analysis
- go vet errors: 1 (unused import)
- Complexity violations: 1 (ComplexCalculator)
- File size violations: 1 (large_module.go)
- **Score: ~60-70%** (intentionally below 90% threshold)

### P2 Tests
- Total: 8 tests
- Passing: 6
- Failing: 2
- **Score: 75%** (intentionally below 85% threshold)

### P3 Coverage
- Overall: ~40-50%
- Gaps: 2 functions with no coverage
- **Needs**: Tests for AdvancedMath(), HandleEdgeCases()
