/**
 * Calculator module with intentional issues for testing.
 */

// ISSUE: Unused import
import * as path from 'path';

export function add(a: number, b: number): number {
  return a + b;
}

export function subtract(a: number, b: number): number {
  return a - b;
}

// ISSUE: Missing return type annotation (TypeScript warning)
export function multiply(a: number, b: number) {
  return a * b;
}

export function divide(a: number, b: number): number {
  if (b === 0) {
    throw new Error('Cannot divide by zero');
  }
  return a / b;
}

// ISSUE: High cyclomatic complexity (> 10)
export function complexCalculator(
  operation: string,
  a: number,
  b: number,
  c?: number
): number {
  let result = 0;

  if (operation === 'add') {
    result = a + b;
  } else if (operation === 'subtract') {
    result = a - b;
  } else if (operation === 'multiply') {
    result = a * b;
  } else if (operation === 'divide') {
    if (b === 0) throw new Error('Division by zero');
    result = a / b;
  } else if (operation === 'power') {
    result = Math.pow(a, b);
  } else if (operation === 'sqrt') {
    if (a < 0) throw new Error('Cannot sqrt negative');
    result = Math.sqrt(a);
  } else if (operation === 'modulo') {
    if (b === 0) throw new Error('Modulo by zero');
    result = a % b;
  } else if (operation === 'triple_add') {
    if (c === undefined) throw new Error('Need c for triple_add');
    result = a + b + c;
  } else if (operation === 'triple_multiply') {
    if (c === undefined) throw new Error('Need c for triple_multiply');
    result = a * b * c;
  } else if (operation === 'average') {
    if (c === undefined) {
      result = (a + b) / 2;
    } else {
      result = (a + b + c) / 3;
    }
  } else {
    throw new Error(`Unknown operation: ${operation}`);
  }

  return result;
}

// NO COVERAGE: This function is never tested
export function advancedMath(x: number, y: number): number {
  if (x > y) {
    return x ** 2 + y ** 2;
  } else if (x < y) {
    return Math.sqrt(Math.abs(x)) + Math.sqrt(Math.abs(y));
  } else {
    return x * y;
  }
}

// NO COVERAGE: Edge case handler
export function handleEdgeCases(value: number | null): number {
  if (value === null) {
    return 0;
  }
  if (value < 0) {
    return Math.abs(value);
  }
  if (value > 1000) {
    return 1000;
  }
  return value;
}
