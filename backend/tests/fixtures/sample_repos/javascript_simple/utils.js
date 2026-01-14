/**
 * Utility functions for the sample application.
 */

export function calculateProduct(numbers) {
  return numbers.reduce((acc, num) => acc * num, 1);
}

export function formatMessage(label, value) {
  return `${label}: ${value}`;
}
