// Package main provides calculator functionality with intentional issues for testing.
package main

import (
	"errors"
	"fmt" // ISSUE: Unused import
	"math"
)

// Add returns the sum of two numbers.
func Add(a, b int) int {
	return a + b
}

// Subtract returns the difference of two numbers.
func Subtract(a, b int) int {
	return a - b
}

// Multiply returns the product of two numbers.
func Multiply(a, b int) int {
	return a * b
}

// Divide returns the quotient of two numbers.
func Divide(a, b float64) (float64, error) {
	if b == 0 {
		return 0, errors.New("cannot divide by zero")
	}
	return a / b, nil
}

// ComplexCalculator performs various operations with HIGH COMPLEXITY.
// ISSUE: Cyclomatic complexity > 10
func ComplexCalculator(operation string, a, b float64, c *float64) (float64, error) {
	var result float64

	if operation == "add" {
		result = a + b
	} else if operation == "subtract" {
		result = a - b
	} else if operation == "multiply" {
		result = a * b
	} else if operation == "divide" {
		if b == 0 {
			return 0, errors.New("division by zero")
		}
		result = a / b
	} else if operation == "power" {
		result = math.Pow(a, b)
	} else if operation == "sqrt" {
		if a < 0 {
			return 0, errors.New("cannot sqrt negative")
		}
		result = math.Sqrt(a)
	} else if operation == "modulo" {
		if b == 0 {
			return 0, errors.New("modulo by zero")
		}
		result = math.Mod(a, b)
	} else if operation == "triple_add" {
		if c == nil {
			return 0, errors.New("need c for triple_add")
		}
		result = a + b + *c
	} else if operation == "triple_multiply" {
		if c == nil {
			return 0, errors.New("need c for triple_multiply")
		}
		result = a * b * *c
	} else if operation == "average" {
		if c == nil {
			result = (a + b) / 2
		} else {
			result = (a + b + *c) / 3
		}
	} else {
		return 0, fmt.Errorf("unknown operation: %s", operation)
	}

	return result, nil
}

// AdvancedMath performs advanced mathematical operations.
// NO COVERAGE: This function is never tested.
func AdvancedMath(x, y float64) float64 {
	if x > y {
		return x*x + y*y
	} else if x < y {
		return math.Sqrt(math.Abs(x)) + math.Sqrt(math.Abs(y))
	} else {
		return x * y
	}
}

// HandleEdgeCases handles edge cases for input values.
// NO COVERAGE: This function is never tested.
func HandleEdgeCases(value *int) int {
	if value == nil {
		return 0
	}
	if *value < 0 {
		return -*value
	}
	if *value > 1000 {
		return 1000
	}
	return *value
}
