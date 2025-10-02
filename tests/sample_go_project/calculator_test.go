package main

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// PASSING TESTS
func TestAdd(t *testing.T) {
	assert.Equal(t, 5, Add(2, 3))
	assert.Equal(t, 0, Add(-1, 1))
	assert.Equal(t, 0, Add(0, 0))
}

func TestSubtract(t *testing.T) {
	assert.Equal(t, 2, Subtract(5, 3))
	assert.Equal(t, -5, Subtract(0, 5))
}

func TestMultiply(t *testing.T) {
	assert.Equal(t, 12, Multiply(3, 4))
	assert.Equal(t, 0, Multiply(0, 5))
}

// FAILING TEST - Intentional failure
func TestDivide(t *testing.T) {
	result, err := Divide(10, 2)
	assert.NoError(t, err)
	assert.Equal(t, 5.0, result)

	result, err = Divide(9, 3)
	assert.NoError(t, err)
	assert.Equal(t, 3.0, result)

	result, err = Divide(7, 2)
	assert.NoError(t, err)
	assert.Equal(t, 3.5, result)

	// FAILURE: Wrong assertion
	result, err = Divide(10, 4)
	assert.NoError(t, err)
	assert.Equal(t, 3.0, result) // Should be 2.5, this will FAIL
}

func TestDivideByZero(t *testing.T) {
	_, err := Divide(10, 0)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "cannot divide by zero")
}

// PARTIAL COVERAGE - ComplexCalculator only tested for some operations
func TestComplexCalculatorAdd(t *testing.T) {
	result, err := ComplexCalculator("add", 5, 3, nil)
	assert.NoError(t, err)
	assert.Equal(t, 8.0, result)
}

func TestComplexCalculatorMultiply(t *testing.T) {
	result, err := ComplexCalculator("multiply", 4, 5, nil)
	assert.NoError(t, err)
	assert.Equal(t, 20.0, result)
}

// FAILING TEST - Wrong expectation
func TestComplexCalculatorPower(t *testing.T) {
	result, err := ComplexCalculator("power", 2, 3, nil)
	assert.NoError(t, err)
	// FAILURE: Wrong expected value
	assert.Equal(t, 6.0, result) // Should be 8.0, this will FAIL
}

// NO TESTS for:
// - AdvancedMath() -> NO COVERAGE
// - HandleEdgeCases() -> NO COVERAGE
// - ComplexCalculator() other operations -> PARTIAL COVERAGE
