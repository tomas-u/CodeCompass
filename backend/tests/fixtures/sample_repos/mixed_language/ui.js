/**
 * UI utilities for displaying data.
 */

export async function fetchData(itemId) {
  const response = await fetch(`/data/${itemId}`);
  return response.json();
}

export function displayResult(data) {
  console.log('Data:', data);
}
