/**
 * API Configuration
 *
 * Centralized configuration for API client
 */

export const API_CONFIG = {
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 120000, // 120 seconds (LLM responses can be slow)
  headers: {
    'Content-Type': 'application/json',
  },
} as const;

export const POLLING_INTERVALS = {
  analysis: 2000, // Poll analysis progress every 2 seconds
  default: 5000,  // Default polling interval
} as const;
