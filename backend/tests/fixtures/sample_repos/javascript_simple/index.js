/**
 * Sample JavaScript application for testing code analysis.
 */

import { calculateProduct, formatMessage } from './utils.js';

function main() {
  const numbers = [2, 3, 4, 5];
  const product = calculateProduct(numbers);
  const message = formatMessage('Product', product);
  console.log(message);
  return 0;
}

// Run main function
main();
