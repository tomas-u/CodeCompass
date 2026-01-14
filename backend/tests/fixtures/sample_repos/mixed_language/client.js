/**
 * Frontend client for the API.
 */

import { fetchData, displayResult } from './ui.js';

async function loadData(itemId) {
  try {
    const data = await fetchData(itemId);
    displayResult(data);
  } catch (error) {
    console.error('Failed to load data:', error);
  }
}

export { loadData };
