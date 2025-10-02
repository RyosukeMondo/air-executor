/**
 * Tests for calculator module.
 */

import {
  add,
  subtract,
  multiply,
  divide,
  complexCalculator
} from './calculator';

// PASSING TESTS
describe('Calculator', () => {
  describe('add', () => {
    it('should add two positive numbers', () => {
      expect(add(2, 3)).toBe(5);
    });

    it('should add negative and positive', () => {
      expect(add(-1, 1)).toBe(0);
    });

    it('should add zeros', () => {
      expect(add(0, 0)).toBe(0);
    });
  });

  describe('subtract', () => {
    it('should subtract numbers', () => {
      expect(subtract(5, 3)).toBe(2);
    });

    it('should handle negative results', () => {
      expect(subtract(0, 5)).toBe(-5);
    });
  });

  describe('multiply', () => {
    it('should multiply numbers', () => {
      expect(multiply(3, 4)).toBe(12);
    });

    it('should handle zero', () => {
      expect(multiply(0, 5)).toBe(0);
    });
  });

  // FAILING TEST - Intentional failure
  describe('divide', () => {
    it('should divide numbers', () => {
      expect(divide(10, 2)).toBe(5);
      expect(divide(9, 3)).toBe(3);
      expect(divide(7, 2)).toBe(3.5);
      // FAILURE: Wrong assertion
      expect(divide(10, 4)).toBe(3); // Should be 2.5, this will FAIL
    });

    it('should throw on division by zero', () => {
      expect(() => divide(10, 0)).toThrow('Cannot divide by zero');
    });
  });

  // PARTIAL COVERAGE - complexCalculator only tested for some operations
  describe('complexCalculator', () => {
    it('should handle add operation', () => {
      expect(complexCalculator('add', 5, 3)).toBe(8);
    });

    it('should handle multiply operation', () => {
      expect(complexCalculator('multiply', 4, 5)).toBe(20);
    });

    // FAILING TEST - Wrong expectation
    it('should handle power operation', () => {
      // FAILURE: Wrong expected value
      expect(complexCalculator('power', 2, 3)).toBe(6); // Should be 8, FAILS
    });
  });
});

// NO TESTS for:
// - advancedMath() -> NO COVERAGE
// - handleEdgeCases() -> NO COVERAGE
// - complexCalculator() other operations -> PARTIAL COVERAGE
